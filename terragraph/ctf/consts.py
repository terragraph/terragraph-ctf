#!/usr/bin/env python3

# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

"""
Constants.
"""
from typing import Dict

TgCtfConsts: Dict = {
    # Full Kafka endpoint URL, e.g. "PLAINTEXT://[2001::1]:9096",
    "DEFAULT_KAFKA_ENDPOINT": "",
    # Fluentd hostname/IP, e.g. "2001::2"
    "DEFAULT_FLUENTD_HOST": "",
    # Fluentd port
    "DEFAULT_FLUENTD_PORT": 24224,
    # RADIUS server IP, e.g. "2001::3"
    "DEFAULT_RADIUS_SERVER_IP": "",
    # Full qualified link to grafana dashboard, e.g. https://host_name/grafana/d/
    "DEFAULT_GRAFANA_ENDPOINT": "",
    # Full qualified link to kibana dashboard, e.g. https://host_name/kibana/app/",
    "DEFAULT_KIBANA_ENDPOINT": "",
    # ElasticSearch endpoint which ends with /
    "DEFAULT_ELASTICSEARCH_ENDPOINT": "",
    # Prometheus endpoint which ends with /
    "DEFAULT_PROMETHEUS_ENDPOINT": "",
    # Proxy server connection details
    # {
    #     "ip_address": "2001::1",
    #     "username": "user123",
    #     "password": "pass123",
    #     "port": "22",
    #     "prompt": "#",
    #     "timeout": 60,
    #     "custom_channel_processing": False,
    #     "jump_host": None,
    #     "shell_family": None,
    # }
    "NMS_PROXY_SERVER": None,
}
