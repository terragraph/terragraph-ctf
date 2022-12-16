#!/usr/bin/env python3

# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

from argparse import Namespace
from datetime import datetime, timedelta, timezone
from io import StringIO
from typing import Any, Dict, List, Optional

import pandas as pd
from ctf.ctf_client.runner.exceptions import DeviceCmdError, TestFailed
from terragraph.ctf.tests.routing.attenuator_odroid import AttenuatorOdroid


class RoutingUtils(AttenuatorOdroid):
    def __init__(self, args: Namespace) -> None:
        super().__init__(args)
        self.host_time_ms: int = 0

    def show_openr_current_logs(self) -> None:

        futures: Dict = self.run_cmd("cat /var/log/openr/current")
        for result in self.wait_for_cmds(futures):
            if not result["success"]:
                raise DeviceCmdError(
                    f"Failed to read openr current log from node {result['node_id']}"
                )
            self.log_to_ctf(
                f"openr current log from node {result['node_id']}: \n{result['message']}"
            )
        return

    def record_host_time(self) -> None:
        """
        Records host machine date and time as a timestamp in milli seconds and in UTC.
        This method is called before changing the MCS value to record the event time.
        """
        host_datetime = datetime.now(tz=timezone.utc)
        self.log_to_ctf(f"host date time in UTC: {host_datetime}", "info")
        self.host_time_ms = int(host_datetime.timestamp() * 1000)
        self.log_to_ctf(
            f"recorded host timestamp in milli secs: {self.host_time_ms}", "info"
        )
        return

    def collect_matching_logs_from_tg_nodes(
        self,
        nodes: List[int],
        search_pattern: str,
        loc_path: str,
        filter: Optional[str] = None,
    ) -> Dict[int, Any]:
        """
        collects logs from each node matching the search pattern, loc path and filter.
        """

        logs_each_node: dict[int, Any] = {}
        command_collect_logs = f"grep -r '{search_pattern}' {loc_path}"
        if filter is not None:
            command_collect_logs += f" | grep {filter}"

        futures: Dict = self.run_cmd(command_collect_logs, nodes)
        for result in self.wait_for_cmds(futures):
            if not result["success"]:
                error_msg = (
                    f"Node {result['node_id']}: {command_collect_logs} returned without results: "
                    + f"{result['error']}"
                )
                self.log_to_ctf(error_msg, "error")
                logs_each_node[result["node_id"]] = None
            else:
                logs_each_node[result["node_id"]] = result["message"]

        return logs_each_node

    def combine_logs_to_data_frame(
        self,
        event,
        reference_time: datetime,
        node_logs: Dict[int, Any],
        data_delimiter: Optional[str] = " ",
    ) -> pd.DataFrame:
        """
        Combines input node logs into panda data frame with node_id and
        date & time columns added.
        """

        list_df: list = []
        for node in node_logs:
            try:
                df = pd.read_csv(
                    StringIO(node_logs[node]),
                    delimiter=data_delimiter,
                    header=None,
                    engine="python",
                )
                df["node"] = node
                list_df.append(df)
            except pd.errors.EmptyDataError:
                # handle empty data frame for node without matching logs
                continue

        m_df = pd.concat(list_df)
        m_df["date"] = m_df[0].str.split("I").str.get(1)
        m_df["datetime"] = reference_time.strftime("%Y") + m_df["date"] + " " + m_df[1]
        m_df["datetime"] = pd.to_datetime(m_df["datetime"], utc=True)
        m_df["timediff_ref"] = m_df["datetime"] - pd.to_datetime(
            reference_time, utc=True
        )
        self.log_to_ctf(
            f"combined data frame for all nodes :\n{m_df.to_string()}",
            "info",
        )

        return m_df

    def create_event_data_frame(
        self,
        event,
        tg_nodes: List[int],
        reference_time: int,
        secs_range_min_max: List[int],
        override_metric_val: Optional[int] = None,
    ) -> pd.DataFrame:
        """
        creates panda event data frame for given input nodes and event.

        logs Vs event:
              event: LINK_DOWN (ROU5)
              * node logs are filtered for message "is DOWN and has backoff",for the date string in format Immyy and at the location /var/log/openr/current.
              event: MCS_CONVERGENCE (ROU6)
              * node logs are filtered for message "Overriding metric for interface",for the date string in format Immyy and at the location /var/log/openr/current.
              event: BACKOFF (ROU7)
              * node logs are filtered for message "is DOWN and has backoff", with "messages" filter and at the location /var/log/openr/current.
              event: MCS_COST (ROU8)
              * node logs are filtered for message "is DOWN and has backoff",for the date string in format Immyy and at the location /var/log/openr/current.
              event: ROUTE_UPDATE (ROU5 & ROU6)
              * node logs are filtered for message "Processing route add/update for",for the date string in format Immyy and at the location /var/log/openr/current.
        """

        # default values
        data_delimiter: str = r"\s+"
        reference_time_s = datetime.utcfromtimestamp(reference_time / 1000)
        date_str: str = reference_time_s.strftime("I%m%d")

        if event == "MCS_CONVERGENCE" or event == "MCS_COST":
            search_pattern = "Overriding metric for interface"
        elif event == "ROUTE_UPDATE":
            search_pattern = "Processing route add/update for"
            data_delimiter = r"[ -]"
        # case for events LINK_DOWN and BACKOFF
        else:
            search_pattern = "is DOWN and has backoff"

        event_node_logs = self.collect_matching_logs_from_tg_nodes(
            nodes=tg_nodes,
            search_pattern=search_pattern,
            loc_path="/var/log/openr/current",
            filter=date_str,
        )
        event_df = self.combine_logs_to_data_frame(
            event=event,
            reference_time=reference_time_s,
            node_logs=event_node_logs,
            data_delimiter=data_delimiter,
        )

        if event == "BACKOFF":
            # column#12 shows backoff time in milli secs in the log/data frame
            event_df["backoff"] = event_df[12].str.replace("ms", "").astype(int)
        else:
            if event == "ROUTE_UPDATE":
                # below statement applies filter on data frame to analyze logs only with
                # route add/update for value > 0 (column#9) and route delete for value = 0 (column#17).
                event_df = event_df.loc[(event_df[9] > 0) & (event_df[17] == 0)]
                self.log_to_ctf(
                    "data frame with route add/update for value > 0 and "
                    + f"route delete for value = 0 :\n{event_df.to_string()}",
                    "info",
                )
            # for cases of MCS_CONVERGENCE, MCS_COST, and LINK_DOWN_CONVERGENCE
            if event == "MCS_CONVERGENCE" or event == "MCS_COST":
                # column#10 shows override metric that is mcs value set from test_options["configs"][0]["value"]
                event_df = event_df.loc[event_df[10] == override_metric_val]

            event_df = event_df.loc[
                (event_df.timediff_ref > timedelta(seconds=secs_range_min_max[0]))
                & (event_df.timediff_ref < timedelta(seconds=secs_range_min_max[1]))
            ]
            # reset indexes here otherwise contains duplicate index numbers
            event_df = event_df.reset_index()
            # apply minimum function on datetime and group by node
            event_df = event_df.loc[event_df.groupby("node")["datetime"].idxmin()]

        self.log_to_ctf(
            f"event data frame for the event {event}:\n{event_df.to_string()}", "info"
        )

        missing_nodes = set(event_df["node"]) - set(tg_nodes)
        if missing_nodes:
            raise TestFailed(
                f"Unexpected missing nodes {missing_nodes} from {event} logs",
                "info",
            )

        return event_df

    def get_all_node_route_update_timediff(
        self,
        tg_action_nodes: List[int],
        tg_nodes: List[int],
        event_df,
        secs_range_min_max,
        reference_time_ms: int,
    ) -> pd.DataFrame:
        """
        Get "ROUTE_UPDATE" event for all the nodes and compute the route times
        relative to the event time in action nodes which are node1 and node2.
        """

        rt_df = self.create_event_data_frame(
            event="ROUTE_UPDATE",
            tg_nodes=tg_nodes,
            reference_time=reference_time_ms,
            secs_range_min_max=secs_range_min_max,
        )

        min_node_change_time = min(
            event_df[tg_action_nodes[0]], event_df[tg_action_nodes[1]]
        )

        # substract routing update timestamp with MCS change/Link down event timestamp
        rt_df["timediff_node1"] = rt_df["datetime"] - event_df[tg_action_nodes[0]]
        rt_df["timediff_node2"] = rt_df["datetime"] - event_df[tg_action_nodes[1]]
        rt_df["timediff_nodes_min"] = rt_df["datetime"] - min_node_change_time
        rt_df[
            ["timediff_node1", "timediff_node2", "timediff_nodes_min", "timediff_ref"]
        ] = abs(
            rt_df[
                [
                    "timediff_node1",
                    "timediff_node2",
                    "timediff_nodes_min",
                    "timediff_ref",
                ]
            ]
        )
        # apply maximum function on these columns
        maxdiffs = rt_df[
            ["timediff_node1", "timediff_node2", "timediff_nodes_min", "timediff_ref"]
        ].max()

        self.log_to_ctf(
            f"\n{maxdiffs.index[0]} : {round(maxdiffs.iloc[0].total_seconds(), 3)}s"
            + f"\n{maxdiffs.index[1]} : {round(maxdiffs.iloc[1].total_seconds(), 3)}s"
            + f"\n{maxdiffs.index[2]} : {round(maxdiffs.iloc[2].total_seconds(), 3)}s"
            + f"\n{maxdiffs.index[3]} : {round(maxdiffs.iloc[3].total_seconds(), 3)}s",
            "info",
        )

        return maxdiffs

    def verify_route_test_results(
        self,
        event: str,
        tg_nodes: List[int],
        tg_action_nodes: List[int],
        expected_time_s: float,
        override_metric_val: Optional[int] = None,
    ) -> None:
        """
        event: LINK_DOWN (ROU5)
              -> Uses node logs for link down to verify that link went down soon after attenuation up.
              -> Uses the attenuation up time as reference time-of-change.
              -> Uses node logs for route add/update to check time new routes were added.
              -> Checks time difference between reference time-of-change and route add for all nodes in fig8.

        event: MCS_CONVERGENCE (ROU6)
              -> Uses node logs for MCS change to verify that MCS and cost changed soon after config change by the controller.
              -> Uses the MCS change log time stamps as reference time-of-change because host time is a poorer reference.
              -> Uses node logs for route add/update to check time new routes were added.
              -> Checks time difference between reference time-of-change and route add for all nodes in fig8.

        event: BACKOFF (ROU7)
              -> Uses node logs for link down and backoff to verify that link went down with backoff time applied after attenuation up.
              -> Verifies that max backoff time on each node is greater than the threshold value of link_backoff_time_s

        event: MCS_COST (ROU8)
              -> Uses node logs for MCS change to verify that MCS and cost changed soon after config change by the controller.
        """

        # short time range for link down event because attenuator returns exact event time.
        short_time_range = [-1, 5]

        # long time range for MCS change event because node(s) override takes time, and
        # we are recording host time right after the node(s) override.
        long_time_range = [-15, 15]

        # default values
        reference_time_ms = self.host_time_ms
        secs_range_min_max = long_time_range
        # case for LINK_DOWN_CONVERGENCE
        if event == "LINK_DOWN_CONVERGENCE":
            reference_time_ms = self.atten_up_time_ms
            secs_range_min_max = short_time_range

        event_df = self.create_event_data_frame(
            event=event,
            tg_nodes=tg_action_nodes,
            reference_time=reference_time_ms,
            secs_range_min_max=secs_range_min_max,  # not used for BACKOFF
            override_metric_val=override_metric_val,
        )

        if event == "BACKOFF":
            event_df = event_df.groupby("node")["backoff"].max()
            self.log_to_ctf(
                f"Max backoff times:\n{event_df.to_string()}",
                "info",
            )
            for node in tg_action_nodes:
                # backoff time in even data frame is in msecs, so convert expected time to msecs before comparison
                if event_df[node] < (expected_time_s * 1000 - 1):
                    raise TestFailed(
                        f"Backoff time is less than expected minimum backoff time in node {node}"
                        + f" with backoff time of {event_df[node]}"
                    )
            return

        # to refer min datetime by node number
        event_df = event_df.groupby("node")["datetime"].min()

        if event == "MCS_COST":
            try:
                self.log_to_ctf(
                    f"MCS-override log time:\n Node {tg_action_nodes[0]} :{event_df[tg_action_nodes[0]]}\n"
                    + f"Node {tg_action_nodes[1]} :{event_df[tg_action_nodes[1]]}\n",
                    "info",
                )
            except pd.errors.EmptyDataError:
                raise TestFailed(
                    f"No MCS-override log found within time window for Node {tg_action_nodes[0]} or {tg_action_nodes[1]}"
                )
            return

        # for cases of event MCS_CONVERGENCE or LINK_DOWN_CONVERGENCE
        maxdiffs = self.get_all_node_route_update_timediff(
            tg_action_nodes, tg_nodes, event_df, secs_range_min_max, reference_time_ms
        )

        if (
            event == "MCS_CONVERGENCE"
            and maxdiffs["timediff_nodes_min"].total_seconds() > expected_time_s
        ):
            raise TestFailed(
                f"timediff_nodes_min is greater than expected re-route convergence time of {expected_time_s} after mcs change event"
            )
        # case of the link down convergence event
        elif (
            event == "LINK_DOWN_CONVERGENCE"
            and maxdiffs["timediff_ref"].total_seconds() > expected_time_s
        ):
            raise TestFailed(
                f"timediff_ref is greater than expected re-route convergence time of {expected_time_s} after link down event"
            )

        return
