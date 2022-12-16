#!/usr/bin/env python3

# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import argparse
import logging
import subprocess
import sys

logger = logging.getLogger(__name__)


env_name = "ctf_client_env"

parser = argparse.ArgumentParser(
    description="Creates python virtual environment to run CTF client tests."
)
parser.add_argument(
    "-n",
    "--name",
    type=str,
    help=f"Name of python virtual environment. If none given, default name of {env_name} is used.",
)

args = parser.parse_args()

if args.name:
    env_name = args.name

logger.info("Check if python3 installed on system.")
output = subprocess.check_output("which python3", shell=True, universal_newlines=True)

# Exit if not found
if "python3" not in output:
    logger.error("Please install python3 before running this script.")
    sys.exit()

logger.info(f"Create virtual environment: {env_name}")
subprocess.check_output(
    f"python3 -m venv ~/{env_name}", shell=True, universal_newlines=True
)

logger.info("Install required packages to run CTF client tests.")
logger.debug(
    subprocess.check_output(
        f"source ~/{env_name}/bin/activate; pip install -r requirements.txt; pip install -r ../common/requirements.txt",
        shell=True,
        universal_newlines=True,
    )
)

logger.debug(
    f"Use command: source ~/{env_name}/bin/activate to activate the environment."
)
