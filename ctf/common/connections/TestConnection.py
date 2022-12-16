# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import getopt
import logging
import sys

from SSHConnection import SSHConnection


def main(argv):
    ip = "2001::1"
    user = "root"
    pwd = "password1"
    # prompt = "root@#"

    logging.basicConfig(
        datefmt="%Y-%m-%d %H:%M:%S",
        format="%(asctime)s %(levelname)-8s %(message)s",
        level=logging.INFO,
    )
    logger = logging.getLogger("ctf.common.connections.SSHConnectionTest")

    try:
        opts, args = getopt.getopt(
            argv,
            "hi:u:p:t:",
            ["help", "hostname=", "username=", "password=", "prompt="],
        )
    except getopt.GetoptError:
        logger.info(
            "TestConnection.py -i <host> -u <username> -p <password>, -t <prompt>"
        )
        sys.exit(2)

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            logger.info(
                "TestConnection.py -i <host> -u <username> -p <password>, -t <prompt>"
            )
            sys.exit()
        elif opt in ("-i", "--hostname"):
            ip = arg
        elif opt in ("-u", "--username"):
            user = arg
        elif opt in ("-p", "--password"):
            pwd = arg
        # elif opt in ("-t", "--prompt"):
        # prompt = arg

    logger.info("--------------SSH TEST ------------------------")
    ssh_obj = SSHConnection(
        in_ip_address=ip,
        in_user=user,
        in_password=pwd,
        login_timeout=60,
    )
    output = ssh_obj.send_command("lspci")
    logger.info(output["message"])

    output = ssh_obj.send_command("pwd")
    logger.info(output["message"])


if __name__ == "__main__":
    main(sys.argv[1:])
