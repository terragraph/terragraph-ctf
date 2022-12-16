# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import glob
import logging
import os
import re
import threading
import time
from stat import S_ISDIR, S_ISREG

import paramiko
from ctf.common.connections.constants import (
    DEFAULT_TIMEOUT_SECONDS,
    LF,
    ShellFamilyName,
)
from ctf.common.connections.ThreadSafeSshConnection import ThreadSafeSshConnection
from ctf.common.helper_functions import create_full_path
from scp import SCPException

logging.getLogger("paramiko").setLevel(logging.WARNING)


logger = logging.getLogger(__name__)


SHELL_VERSION_CMD_SWITCHER = {
    ShellFamilyName.BOURNE: 'if ! [ -z $BASH_VERSION ]; then echo "bash:$BASH_VERSION"; elif ! [ -z $ZSH_VERSION ]; then echo "zsh:$ZSH_VERSION"; else echo ""; fi',
    ShellFamilyName.POWERSHELL: 'echo "pwsh:$($PSVersionTable.PSVersion.ToString())"',
}

SHELL_VERSION_SWITCHER = {
    "bash": 4,
    "zsh": 5,
    "pwsh": 7,
}


def _is_shell_version_compatible(version: str) -> bool:
    if not version:
        return False
    split_version = version.split(":")
    return (
        int(split_version[1][0]) >= SHELL_VERSION_SWITCHER.get(split_version[0]),
        split_version[0],
    )


# TODO Subclass ThreadSafeSshConnection
class SSHConnection(object):
    def __init__(
        self,
        in_ip_address,
        in_user,
        in_password,
        in_prompt=None,
        in_private_key=None,
        login_timeout=DEFAULT_TIMEOUT_SECONDS,
        port=22,
        is_jump_host=False,
        inj_ipj_public_address=None,
        inj_user=None,
        inj_password=None,
        inj_ipj_private_address=None,
        shell_family_name=None,
        custom_channel_processing=False,
        ssh_agent=True,
        scp=None,  # FIXME Unused
        sftp=None,  # FIXME Unused
        available_ports="22",
        inj_private_key=None,
        connect_retry_interval_sec=0.0,
    ):
        """
        SSH connection class use for connecting node using SSH protocol.
        It have methods to send command to remote end And also have capability
        Jump-host
        :param in_ip_address: ip address of remote node
        :param in_user: user of remote node
        :param in_password: password of remote node
        :param in_prompt: prompt of remote node
        :param in_private_key: string key of the private key to use with remote node
        :param login_timeout: timeout for login
        :param port: ssh port
        :param is_jump_host: flag for jump host
        :param inj_ipj_public_address: public ip address of jump host
        :param inj_user: user of jump host
        :param inj_password: password of jump host
        :param inj_ipj_private_address: private ip address of jump host
        :param inj_private_key: string key of the private key to use for jump host
        :param shell_family_name: flag for shell family name
        :param custom_channel_processing: flag for custom channel processing (used by consumers to enable any special processing desired)
        :param connect_retry_interval_sec: interval between connect re-tries (in effect only when not zero)
        """
        super().__init__()
        # Define the properties
        self.ip_address = in_ip_address
        self.user = in_user
        self.password = in_password
        self.prompt = in_prompt
        self.is_jump_host = is_jump_host
        self.login_timeout = login_timeout
        self.port = port
        self.inj_ipj_public_address = inj_ipj_public_address
        self.inj_user = inj_user
        self.inj_password = inj_password
        self.inj_ipj_private_address = inj_ipj_private_address
        self.shell_family_name = shell_family_name
        self.custom_channel_processing = custom_channel_processing
        self.ssh = None  # thread safe ssh connection
        self.logs = []  # FIXME not thread safe
        self.ssh_agent = ssh_agent
        self.available_ports = int(available_ports) if available_ports else 22
        self.verbose_logs = False
        self.sftp_enabled = True
        self.private_key = in_private_key
        self.inj_private_key = inj_private_key
        self.connect_retry_interval_sec = connect_retry_interval_sec

    # TODO Remove once superclass is ThreadSafeSshConnection
    def enable_sftp(self, enable):
        self.sftp_enabled = enable
        if self.ssh is not None:
            self.ssh.sftp_enabled = enable

    # TODO Remove once superclass is ThreadSafeSshConnection
    def enable_verbose_logs(self, enable):
        self.verbose_logs = enable
        if self.ssh is not None:
            self.ssh.verbose_logs = enable

    # TODO Remove once superclass is ThreadSafeSshConnection
    def _debug_log(self, s, result=None):
        if self.verbose_logs:
            m = f"{s} | thread {threading.get_native_id()} | ip {self.ip_address}"
            if result is None:
                logger.info(m)
            else:
                logger.info(f"{m} | result {result}")

    def _can_use_interactive_mode(self) -> ():
        if self.shell_family_name:
            use_interactive_mode = True
        else:
            use_interactive_mode = False
        reason = ""

        shell_name = ""

        if use_interactive_mode:
            (_out, _, _rc) = self.ssh.exec(
                SHELL_VERSION_CMD_SWITCHER.get(self.shell_family_name)
            )
            reason = "Shell Family set"
            if _rc == 0 and _out:
                use_interactive_mode, shell_name = _is_shell_version_compatible(_out)
                if use_interactive_mode:
                    reason += f" and shell is supported: {_out}"
                else:
                    reason += f" but shell is not supported: {_out}"
            else:
                use_interactive_mode = False
                reason += " but shell could not be identified."

        return use_interactive_mode, shell_name, reason.strip(LF)

    def _connect(self, timeout=None):
        """
        Establish a new ssh connection for the calling thread.
        no-op if the calling thread is already connected.
        :return: result dictionary
        """

        result = {}
        result["error"] = 0
        result["message"] = ""
        result["warning"] = 0
        result["connection_error"] = False

        if not timeout:
            timeout = self.login_timeout
        try:
            if self.ssh is None:
                self.ssh = ThreadSafeSshConnection(
                    ip=self.ip_address,
                    port=self.port,
                    username=self.user,
                    password=self.password,
                    prompt=self.prompt,
                    private_key=self.private_key,
                    timeout=timeout,
                    use_ssh_agent=self.ssh_agent,
                    verbose_logs=self.verbose_logs,
                    sftp_enabled=self.sftp_enabled,
                    using_jump_host=self.is_jump_host,
                    jump_host_public_ip=self.inj_ipj_public_address,
                    jump_host_private_ip=self.inj_ipj_private_address,
                    jump_host_username=self.inj_user,
                    jump_host_password=self.inj_password,
                    jump_host_port=self.available_ports,
                    jump_host_private_key=self.inj_private_key,
                )
            self.ssh.connect()  # no-op if calling thread is already connected

            use_interactive_mode, shell_name, reason = self._can_use_interactive_mode()
            if not use_interactive_mode and reason:
                result["warning"] = 1
                result["message"] = reason

        except Exception as e:
            result["error"] = 1
            result["message"] = f"[{type(e).__name__}]: {str(e)}"
            result["connection_error"] = True

        return result

    def connect(self, timeout=None):
        """
        Establish a new ssh connection for the calling thread with retries.
        no-op if the calling thread is already connected.
        :return: result dictionary
        """
        result = {}
        result["error"] = 0
        result["message"] = ""

        try:
            if not timeout:
                timeout = self.login_timeout

            retry_deadline = time.monotonic() + timeout
            while True:
                result = self._connect(timeout)
                if result["error"] == 0 or self.connect_retry_interval_sec <= 0.0:
                    break  # retry not needed or not requested
                # retry if there is enough time left
                timeout = (
                    retry_deadline - time.monotonic() - self.connect_retry_interval_sec
                )
                if timeout <= 0.0:
                    self._debug_log(
                        f"connect | no time left to retry ip {self.ip_address}"
                    )
                    break  # no time left for a retry
                time.sleep(self.connect_retry_interval_sec)
                self._debug_log(f"connect | retrying ip f{self.ip_address}")
        except Exception as e:
            result["error"] = 1
            result["message"] = f"SSH Connection error: {str(e)}"

        return result

    def _send_command(
        self,
        cmd,
        timeout=DEFAULT_TIMEOUT_SECONDS,
        on_process_start=None,
        on_process_stop=None,
        on_stdin_send=None,
        on_stdout_recv=None,
        on_stderr_recv=None,
        check_cancel=None,
        check_cancel_complete=None,
    ):
        """
        Send a shell command and retrieve the response from stdout and stderr
        :param cmd: command
        :type cmd: string
        :param timeout: timeout for command
        :param on_process_start: callback for when started
        :param on_process_stop: callback for when stopped
        :param on_stdin_send: callback for when stdin sent
        :param on_stdout_recv: callback for when stdout received
        :param on_stderr_recv: callback for when stderr received
        :param check_cancel: function to check if cancel requested
        :param check_cancel_complete: function to check if cancel completed
        :type timeout: int or float
        :return: result dictionary
        """
        result = {}
        result["error"] = 0
        result["message"] = ""
        result["returncode"] = 0
        result["stderr"] = ""

        try:
            result = self.connect()
            if result["error"] != 0:
                return result

            use_interactive_mode, shell_name, reason = self._can_use_interactive_mode()
            if not use_interactive_mode and reason:
                logger.warning(reason)

            # '&' is the standard shell command background process operator
            # CTF is currently written to track foreground shell processes only
            # for advanced features like Hard Stop or Live Logs
            if use_interactive_mode and cmd.endswith("&"):
                use_interactive_mode = False
                logger.warning(
                    "Skipping SSH interactive mode since Command will create a background process"
                )

            logger.info(
                f"SSH Send Shell Command will{'' if use_interactive_mode else ' not'} use interactive mode"
            )

            if use_interactive_mode:
                (
                    result["message"],
                    result["stderr"],
                    result["returncode"],
                ) = self.ssh.send(
                    cmd,
                    shell_family_name=self.shell_family_name,
                    shell_name=shell_name,
                    timeout=timeout,
                    on_process_start=on_process_start,
                    on_process_stop=on_process_stop,
                    on_stdin_send=on_stdin_send,
                    on_stdout_recv=on_stdout_recv,
                    on_stderr_recv=on_stderr_recv,
                    check_cancel=check_cancel,
                    check_cancel_complete=check_cancel_complete,
                )
            else:
                (
                    result["message"],
                    result["stderr"],
                    result["returncode"],
                ) = self.ssh.exec(
                    cmd,
                    timeout=timeout,
                )

        except Exception as e:
            result["error"] = 1
            result["message"] = str(e)
        finally:
            self.disconnect()

        if "message" in result:
            self.logs.append(result["message"])
        if "stderr" in result:
            self.logs.append(result["stderr"])

        return result

    def create_folder(self, remote_path):
        result = self.connect()
        if result["error"] != 0:
            return result

        file_stat = None
        try:
            file_stat = self.ssh.sftp(op="stat", path=remote_path)
            result["message"] = f"Already exists: {remote_path}"
        except paramiko.SSHException as e:
            result["error"] = 1
            result["message"] = str(e)
        except IOError as e:
            if file_stat is None:
                try:
                    self.ssh.sftp(op="mkdir", path=remote_path)
                    result["message"] = f"Created: {remote_path}"
                except IOError as e:
                    result["error"] = 2
                    result["message"] = str(e)
            else:
                result["error"] = 3
                result["message"] = str(e)

        return result

    def get_latest_folder(self, remote_path, directories=True):
        result = self.connect()
        if result["error"] != 0:
            return result

        try:
            result["message"] = ""
            files = self.ssh.sftp(op="listdir_attr", path=remote_path)
            files = (
                [f for f in files if S_ISDIR(f.st_mode)]
                if directories
                else [f for f in files if S_ISREG(f.st_mode)]
            )
            if len(files):
                files.sort(key=lambda d: d.st_mtime, reverse=True)
                result["message"] = files[0].filename
        except paramiko.SSHException as e:
            result["error"] = 1
            result["message"] = str(e)
        except IOError as e:
            result["error"] = 2
            result["message"] = str(e)

        return result

    def get_latest_file_in_folder(self, remote_path):
        return self.get_latest_folder(remote_path, directories=False)

    def get_files_in_folder_details(self, remote_path):
        result = self.connect()
        if result["error"] != 0:
            return result

        try:
            files = self.ssh.sftp(op="listdir_attr", path=remote_path)
            result["message"] = files
        except paramiko.SSHException as e:
            result["error"] = 1
            result["message"] = str(e)
        except IOError as e:
            result["error"] = 2
            result["message"] = str(e)

        return result

    def remove_folder_and_files(self, remote_path, level=0, files_only=False):
        result = self.connect()
        if result["error"] != 0:
            return result

        try:
            message = ""
            files = self.ssh.sftp(op="listdir_attr", path=remote_path)
            for f in files:
                rpath = os.path.join(remote_path, f.filename)
                if S_ISDIR(f.st_mode):
                    message += self.remove_folder_and_files(
                        rpath, level=(level + 1), files_only=files_only
                    )["message"]
                else:
                    line = f"{level}-{f.filename}, "
                    message += line
                    self.ssh.sftp(op="remove", path=rpath)

            line = f"{remote_path}, "
            message += line
            if not files_only:
                self.ssh.sftp(op="rmdir", path=remote_path)

            result["message"] = message
        except paramiko.SSHException as e:
            result["error"] = 1
            result["message"] = str(e)
        except IOError as e:
            result["error"] = 2
            result["message"] = str(e)

        return result

    def copy_files_to_remote(self, local_files, remote_path, recursive=True):
        result = self.connect()
        if result["error"] != 0:
            return result

        try:
            self.ssh.scp(
                op="put",
                local_path=local_files,
                recursive=recursive,
                remote_path=remote_path,
            )
            result[
                "message"
            ] = f"Local file(s) copied from: {local_files} to {remote_path}"
        except SCPException as e:
            result["error"] = 1
            result["message"] = str(e)

        return result

    def copy_files_from_remote_sftp(self, local_path, remote_path):
        result = self.connect()
        if result["error"] != 0:
            return result

        try:
            if os.path.isdir(local_path):
                local_path = create_full_path(local_path, remote_path)
            self.ssh.sftp(op="get", path=remote_path, local_path=local_path)
            if os.path.exists(local_path):
                result[
                    "message"
                ] = f"Remote file copied from: {remote_path} to {local_path} via SFTP"
            else:
                raise Exception(
                    f"Remote file NOT copied from: {remote_path} to {local_path} via SFTP"
                )
        except Exception as e:
            raise Exception(
                f"Remote file NOT copied from: {remote_path} to {local_path} via SFTP. "
                + "Received Exception: "
                + str(e)
            )

        return result

    def copy_files_from_remote_glob_sftp(self, local_path, remote_path):
        result = self.connect()
        if result["error"] != 0:
            return result

        try:
            remote_path_dir = os.path.dirname(remote_path.replace("\\", os.sep))
            remote_path_filename = os.path.basename(remote_path.replace("\\", os.sep))
            remote_files = self.ssh.sftp(op="listdir", path=remote_path_dir)
            remote_path_filename = remote_path_filename.replace(".", "\\.")
            remote_path_filename = remote_path_filename.replace("*", ".*")
            for remote_file in remote_files:
                if re.search(rf"{remote_path_filename}", remote_file):
                    local_path_dir = os.path.dirname(local_path)
                    local_path_sftp = os.path.join(local_path_dir, remote_file)
                    remote_path_sftp = os.path.join(remote_path_dir, remote_file)
                    self.copy_files_from_remote_sftp(local_path_sftp, remote_path_sftp)
            if os.path.isdir(local_path):
                local_path = create_full_path(local_path, remote_path)
            if glob.glob(local_path):
                result[
                    "message"
                ] = f"Remote glob file copied from: {remote_path} to {local_path} via SFTP"
            else:
                raise Exception(
                    f"Remote glob file NOT copied from: {remote_path} to {local_path} via SFTP"
                )
        except Exception as e:
            raise Exception(
                f"Remote glob file NOT copied from: {remote_path} to {local_path} via SFTP."
                + "Received Exception: "
                + str(e)
            )

        return result

    def copy_files_from_remote_glob(self, local_path, remote_path):
        result = self.connect()
        if result["error"] != 0:
            return result

        scp_err = f"copy_files_from_remote_glob | scp failed | local_path {local_path} | remote_path {remote_path}"

        try:
            self.ssh.scp("get_glob", remote_path=remote_path, local_path=local_path)
            if os.path.isdir(local_path):
                local_path = create_full_path(local_path, remote_path)
            if glob.glob(local_path):
                result[
                    "message"
                ] = f"copy_files_from_remote_glob | scp ok | local_path {local_path} | remote_path {remote_path}"
            else:
                logger.error(scp_err)
                raise Exception(scp_err)
        except (SCPException, Exception) as e:
            # FIXME Why does scp fail and sftp retry succeed?
            if self.sftp_enabled:
                logger.error(
                    f'copy_files_from_remote_glob | scp caught "{str(e)}" | retrying with sftp'
                )
                result = self.copy_files_from_remote_glob_sftp(local_path, remote_path)
            else:
                result["error"] = 1
                result["message"] = scp_err

        return result

    def copy_files_from_remote(self, local_path, remote_path, recursive=True):
        result = self.connect()
        if result["error"] != 0:
            return result

        try:
            self.ssh.scp(
                op="get",
                remote_path=remote_path,
                local_path=local_path,
                recursive=recursive,
            )
            if os.path.isdir(local_path):
                local_path = create_full_path(local_path, remote_path)
            if not os.path.exists(local_path):
                if "*" in remote_path:
                    result = self.copy_files_from_remote_glob(local_path, remote_path)
                else:
                    result = self.copy_files_from_remote_sftp(local_path, remote_path)
            else:
                result[
                    "message"
                ] = f"Remote file(s) copied from: {remote_path} to {local_path}"
        except SCPException as e:
            # FIXME Why is retry necessary, and how come it works?
            logger.error(f'copy_files_from_remote | caught "{str(e)}" | retrying')
            try:
                if "*" in remote_path:
                    result = self.copy_files_from_remote_glob(local_path, remote_path)
                else:
                    result = self.copy_files_from_remote_sftp(local_path, remote_path)
                result["message"] = str(e) + ". " + result["message"]
            except Exception as e2:
                result["error"] = 1
                result["message"] = str(e) + ". " + str(e2)

        return result

    def disconnect(self):
        """
        Disconnect the calling thread from host.
        no-op if the calling thread is not connected.
        :return: result dictionary
        """
        result = {}
        try:
            if self.ssh is not None:
                self.ssh.disconnect()  # no-op if the calling thread is not connected
        except Exception as e:
            result["error"] = 1
            result["message"] = str(e)

        return result

    def send_command(
        self,
        cmd,
        timeout=DEFAULT_TIMEOUT_SECONDS,
        on_process_start=None,
        on_process_stop=None,
        on_stdin_send=None,
        on_stdout_recv=None,
        on_stderr_recv=None,
        check_cancel=None,
        check_cancel_complete=None,
        split_cmd=False,
    ):
        """
        Main callable function. Execute a shell command.
        :param cmd: command
        :param timeout: timeout for command
        :param on_process_start: callback for when started
        :param on_process_stop: callback for when stopped
        :param on_stdin_send: callback for when stdin send
        :param on_stdout_recv: callback for when stdout received
        :param on_stderr_recv: callback for when stderr received
        :param check_cancel: function to check if cancel requested
        :param check_cancel_complete: function to check if cancel completed
        :return: result dictionary with the following format:
        ```
        {
            "error": <0 = success, 1 = failure>,
            "message": "<stdout>",
            "stderr": "<stderr>",
            "returncode": <int>,
        }
        ```
        """

        def internal_send_cmd(in_cmd):
            return self._send_command(
                in_cmd,
                timeout=timeout,
                on_process_start=on_process_start,
                on_process_stop=on_process_stop,
                on_stdin_send=on_stdin_send,
                on_stdout_recv=on_stdout_recv,
                on_stderr_recv=on_stderr_recv,
                check_cancel=check_cancel,
                check_cancel_complete=check_cancel_complete,
            )

        def append_to_dict_value(key, dict, old_value):
            dict[key] = old_value + dict[key] if dict[key] else old_value

        result_dict = {}
        result_dict["error"] = 0
        result_dict["message"] = ""
        result_dict["returncode"] = 0
        result_dict["stderr"] = ""

        if split_cmd:
            for sub_cmd in cmd.split(";"):
                if check_cancel and check_cancel():
                    break
                sub_cmd = sub_cmd.strip()
                if not sub_cmd:
                    continue

                prev_message = result_dict["message"]
                prev_stderr = result_dict["stderr"]

                result_dict = internal_send_cmd(in_cmd=sub_cmd)

                append_to_dict_value("message", result_dict, prev_message)
                append_to_dict_value("stderr", result_dict, prev_stderr)

                if result_dict["error"] == 1:
                    break
        else:
            result_dict = internal_send_cmd(in_cmd=cmd)

        return result_dict
