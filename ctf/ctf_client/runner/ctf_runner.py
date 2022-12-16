#!/usr/bin/env python3

# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import argparse
import atexit
import logging
import os
import signal
import sys
from typing import Dict, Optional

# NOTE: Keep this above all ctf imports
# EXTERNAL_DEPLOYMENT env flag is used to identify if the CTF instance the ctf_client is connecting to is hosted within fb (i.e Tupperware) or external like TIP
os.environ["EXTERNAL_DEPLOYMENT"] = "True"

from ctf.ctf_client.lib.helper_functions import dict_to_pretty_table

from .lib import CtfHelpers

try:
    # To get login credentials via secrets (Facebook internal)
    from crypto.keychain_service.keychain import ttypes as keychain
    from libfb.py.thrift_clients.keychain_thrift_client import KeychainClient
except Exception as e:
    print(f"{str(e)}")
    pass

# Set paramiko + requests/urllib3 libraries logging to be WARNINGS and above
logging.getLogger("jsonmerge").setLevel(logging.WARNING)
logging.getLogger("paramiko").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)


logger = logging.getLogger(__name__)


class CtfRunner:
    """Helper for launching CTF tests and test suites"""

    def __init__(self, team_id: int, tests: Dict, test_suites: Dict = None) -> None:
        self.team_id = team_id
        self.tests = tests
        self.test_suites = test_suites

    def _get_parser(self) -> argparse.ArgumentParser:
        """Create and return an argparse parser."""

        # Main parser options
        parser = argparse.ArgumentParser(
            description="Run a CTF test.",
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        )
        parser.add_argument(
            "--team-id", default=self.team_id, type=int, help="CTF team ID"
        )
        subparsers = parser.add_subparsers(title="command")

        # "run" subcommand
        run_cmd = subparsers.add_parser("run", help="Run a test")
        run_cmd.add_argument(
            "--debug", action="store_true", help="Enable logging at debug verbosity"
        )
        run_cmd.add_argument(
            "--skip",
            nargs="+",
            choices=("pre_run", "post_run"),
            help="Skip one or many run steps",
        )
        run_cmd.add_argument(
            "--nodes-data",
            help="JSON file containing data for running a test on a specific setup",
        )
        run_cmd.add_argument(
            "--nodes-data-dir",
            help="Directory containing data for running tests on specific setups, "
            + "only used if '--nodes-data' is not provided",
        )
        run_cmd.add_argument(
            "--run-sandcastle",
            action="store_true",
            help="Run test with sandcastle credentials",
        )
        run_cmd.add_argument(
            "--test-setup-id",
            type=int,
            help="Test setup ID in the CTF database (run with 'list-setups' to list them)",
            required=True,
        )
        run_cmd.add_argument(
            "--timeout",
            type=int,
            default=60,
            help="Timeout period for each test step, in seconds",
        )
        run_cmd.add_argument(
            "--log-collect-timeout",
            type=int,
            default=300,
            help="Timeout period for the log file collection step, in seconds",
        )
        run_cmd.add_argument(
            "--scp-timeout",
            type=int,
            default=180,
            help="Timeout period for scp functions, in seconds",
        )
        run_cmd.add_argument(
            "--max-workers", default=10, help="Maximum simultaneous operations"
        )
        run_cmd.add_argument(
            "--no-ssh-debug",
            action="store_true",
            default=False,
            help="Suppress verbose ssh debug logs when --debug is also enabled",
        )
        run_cmd.add_argument(
            "--abort-suite-on-failure",
            action="store_true",
            default=False,
            help="Skip any remaining tests in a suite if a test fails",
        )
        run_cmd.add_argument(
            "--json_args",
            type=str,
            default="",
            help="test case config json overlay/update from the CTF UI",
        )
        run_cmd.add_argument(
            "testname", metavar="<TestName>", help="Test class or suite name"
        )
        run_cmd.add_argument(
            "--test-args",
            nargs="*",
            default=argparse.SUPPRESS,
            help="Optional test-specific arguments in key=value format",
        )
        run_cmd.add_argument(
            "--store-logs-locally",
            nargs="?",
            const="/tmp/ctf_logs/",
            help="Store the logs locally. NOTE: Disk space has to be managed by user.",
        )
        run_cmd.set_defaults(func=self._run_test)

        # "list-tests" subcommand
        list_tests_cmd = subparsers.add_parser(
            "list-tests", help="List all possible tests"
        )
        list_tests_cmd.set_defaults(func=self._list_tests)

        # "list-setups" subcommand
        list_setups_cmd = subparsers.add_parser(
            "list-setups", help="List all of the team's test setups"
        )
        list_setups_cmd.set_defaults(func=self._list_setups)

        # "describe" subcommand
        describe_cmd = subparsers.add_parser("describe", help="Show test details")
        describe_cmd.add_argument(
            "testname", metavar="<TestName>", help="Test class name"
        )
        describe_cmd.set_defaults(func=self._describe_test)

        # "force-free" subcommand
        force_free_cmd = subparsers.add_parser(
            "force-free", help="Forcefully free a test setup"
        )
        force_free_cmd.add_argument(
            "test_setup_id",
            metavar="<test-setup-id>",
            type=int,
            help="Test setup ID in the CTF database",
        )
        force_free_cmd.set_defaults(func=self._force_free_setup)

        # Commands available in CTF serverless mode.
        ctf_serverless_cmds = [run_cmd, list_setups_cmd]
        for cmd in ctf_serverless_cmds:
            cmd.add_argument(
                "--serverless",
                type=str,
                choices=["true", "false"],
                default="false",
                help="If true, uses emulated CTF APIs, otherwise it uses CTF server APIs",
            )
        return parser

    def _get_secret(self, secret) -> Optional[str]:
        req = keychain.GetSecretRequest(name=secret, author=keychain.RequestAuthor())
        try:
            secret = KeychainClient().getSecret(req)
            secret_str = str(secret.secret)
            return secret_str
        except (
            keychain.KeychainServiceException,
            keychain.KeychainClientException,
        ) as e:
            logger.error(f"Keychain Service Exception: {str(e)}")
            return None

    def _exit_handler(self, test) -> None:
        logger.info("_exit_handler triggered")
        # Ignore SIGINT here...
        signal.signal(signal.SIGINT, lambda signal, frame: None)

        test.resource_cleanup()

    def _run_test(self, args) -> int:
        """'run' command handler."""
        # Configure logging
        logging.basicConfig(
            format="[%(asctime)s] %(levelname)s: %(message)s (%(filename)s:%(lineno)d)",
            level=logging.DEBUG if args.debug else logging.INFO,
        )

        # Use Sandcastle login credentials
        if args.run_sandcastle:
            user = self._get_secret("CTF_BUCK_USER")
            password = self._get_secret("CTF_BUCK_PASSWORD")
            api_server_url = self._get_secret("CTF_API_SERVER_URL")
            file_server_url = self._get_secret("CTF_FILE_SERVER_URL")
            if user and password and api_server_url and file_server_url:
                logger.info("Logging in as CTF Test User due to --run-sandcastle flag")
                os.environ["CTF_USER"] = user
                os.environ["CTF_PASSWORD"] = password
                os.environ["CTF_API_SERVER_URL"] = api_server_url
                os.environ["CTF_FILE_SERVER_URL"] = file_server_url
            else:
                logger.error("Failed to fetch all credentials for Sandcastle")
                return -1

        if args.testname in self.tests:
            test = self.tests[args.testname](args)
            # Make sure we free the setup for other tests at exit
            atexit.register(self._exit_handler, test)
            return test.execute()
        elif args.testname in self.test_suites:
            # If it's a test suite, run all the component tests
            return self._run_test_suite(args)
        else:
            # Find the desired test
            logger.error(
                f"{args.testname} not available - type 'list-tests' to print all valid "
                + "test names."
            )
            return -2

    def _run_test_suite(self, args) -> int:
        """Run all the tests in the test suite. Acquire testbed
        only once."""
        test_suite = self.test_suites[args.testname]
        logger.info(
            "\n================================================================\n"
            + f" Starting test suite: {args.testname}\n"
            + "================================================================\n"
        )

        acquire = True
        skip_remaining_tests = False
        test_results = []
        for idx, tc in enumerate(test_suite):
            if skip_remaining_tests:
                test_results.append({"name": tc.__name__, "skipped": True})
                continue

            test = self.tests[tc.__name__](args)
            logger.info(
                "\n----------------------------------------------------------------\n"
                + f" Executing test ({idx+1} of {len(test_suite)}): {test.TEST_NAME}\n"
                + "----------------------------------------------------------------\n"
            )
            if acquire:
                # Acquire testbed on the first test only
                atexit.register(self._exit_handler, test)
            ret = test.execute(acquire)
            test_results.append(
                {"name": tc.__name__, "ret": ret, "url": test.test_url()}
            )
            if ret and args.abort_suite_on_failure:
                skip_remaining_tests = True
                continue

            acquire = False

        logger.info(
            "\n================================================================\n"
            + f" Results for test suite: {args.testname}\n"
            + "================================================================\n"
        )
        suite_ret = 0
        for res in test_results:
            if "skipped" in res:
                logger.info(f"[SKIPPED] {res['name']}")
            else:
                if res["ret"]:
                    suite_ret = res["ret"]
                    status = "FAIL"
                else:
                    status = "PASS"
                logger.info(f"[{status}] {res['name']}: {res['url']}")

        return suite_ret

    def _list_tests(self, args) -> int:
        """'list-tests' command handler."""
        print("Available tests:")
        for test_name, test in self.tests.items():
            print(f"- {test_name}: {test.DESCRIPTION}")

        print("\nAvailable test suites:")
        for name, suite in self.test_suites.items():
            print(f"- {name}:")
            for test in suite:
                print(f"  > {test.TEST_NAME}")
        return 0

    def _list_setups(self, args) -> int:
        """'list-setups' command handler."""
        # NOTE: CTF module already prints a table, so we don't print anything extra.
        ctf_helper = CtfHelpers(args)
        test_setup_list = ctf_helper.list_test_setups(args.team_id)
        # convert the list of json dicts to a human-readable table
        columns = {"id": "ID", "name": "Name", "description": "Description"}
        msg = "test_setups_dir: "
        if not ctf_helper.serverless:
            columns.update({"status": "Status"})
            msg = "selected team: "
        test_setup_list_table = dict_to_pretty_table(test_setup_list, columns)

        print(f"Here is the list of test setup(s) within your {msg}")
        print(test_setup_list_table)
        return 0

    def _describe_test(self, args) -> int:
        """'describe' command handler."""
        if args.testname not in self.tests:
            logger.error(
                f"{args.testname} not available - type 'list-tests' to print all valid "
                + "test names."
            )
            return -1

        test = self.tests[args.testname]
        print(f"{args.testname}: {test.DESCRIPTION}")
        test_params = test.test_params()
        if len(test_params):
            print("\nArguments:")
            for param, metadata in test_params.items():
                text = [metadata["desc"]]
                if "required" in metadata and metadata["required"]:
                    text.append("(required)")
                elif "default" in metadata:
                    text.append(f"(default: {metadata['default']})")
                print(f"- {param}: {' '.join(text)}")

        return 0

    def _force_free_setup(self, args) -> int:
        """'force-free' command handler."""
        ctf_helper = CtfHelpers(args)
        ctf_helper.force_free_test_setup(args.test_setup_id)
        return 0

    def _signal_handler(self, signum=-1, frame=-1) -> None:
        """This will get called when terminate signal is encountered"""
        logger.info(f"Received signal {signum}, exiting...")
        # At this point of time if atexit is registered then the _exit_handler() would be triggered
        sys.exit()

    def run(self) -> int:
        # Parse CLI arguments
        parser = self._get_parser()
        args = parser.parse_args()
        if not args:
            logger.error("Argument parsing error, exiting...")
            return -1
        if not getattr(args, "func", None):
            parser.print_help()
            return 1
        # Register terminate signal for clean exit
        signal.signal(signal.SIGTERM, self._signal_handler)
        return int(args.func(args))


if __name__ == "__main__":
    logger.error("Do not run directly")
