# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

"""
ThreadSafeSshConnection enables multi-threaded applications to manage
    independent connections to one ssh server. Each thread has a connection
    state indexed to its native thread id. The connection state
    includes up to two paramiko SSHClient objects, one for connecting to
    the ssh server, and one for connecting to an optional jump host.

Actual ssh connections are only made when the connect() method is called.

SSH does not provide a way to specify, or identify,
    what type of shell a server will open.

But CTF needs to know, so that it can issue commands with shell specific
    syntax, in order to:
    - identify operating system
    - handle i/o in interactive mode

Therefore, to support extended features, CTF allows devices to specify
    what shell they will open, from these options so far:
    - Bash 4.x+
    - Pwsh 7.x+

It is easiest to support future shells that offer full support for modern
    command pipeline operators:
    - &&
    - ||
"""

import io
import logging
import socket
import threading
import time
from collections import deque
from timeit import default_timer as timer
from typing import Any, Tuple, Union

import ctf.common.constants as constants
import paramiko
from ctf.common.connections.constants import (
    CMD_END_MSG,
    DEFAULT_POLL_DELAY_SECONDS,
    DEFAULT_READ_BYTES,
    DEFAULT_TIMEOUT_CANCEL_SECONDS,
    DEFAULT_TIMEOUT_SECONDS,
    LF,
    RC_CANCEL,
    RC_TIMEOUT,
    ShellFamilyName,
)
from scp import SCPClient

if not constants.IS_EXTERNAL_DEPLOYMENT:
    import pyjk as justknobs

logger = logging.getLogger(__name__)

SHELL_PID_CMD_SWITCHER = {
    ShellFamilyName.BOURNE: "echo $$",
    ShellFamilyName.POWERSHELL: "echo $PID",
}

SHELL_RC_CMD_SWITCHER = {
    ShellFamilyName.BOURNE: "echo $?",
    # PowerShell has $LASTEXITCODE for real codes
    # but it only returns values if last command was
    # a Windows program, not PowerShell cmdlet
    # it would be a lot of work for CTF to be that introspective
    ShellFamilyName.POWERSHELL: "if ($?) {echo 0} else {echo 1}",
}


SHELL_BLOCKING_CMD_SWITCHER = {"bash": "bash -s", "zsh": "zsh -s", "pwsh": "pwsh -c -"}


class State:
    """Connection state of a thread"""

    def __init__(self, thread_id, using_jump_host):
        self.thread_id = thread_id  # for logging convenience only
        self.ssh_client = paramiko.SSHClient()
        self.ssh_client_jump_host = paramiko.SSHClient() if using_jump_host else None
        self.connected = False
        self.scp = None
        self.sftp = None


class ThreadSafeSshConnection:
    """Maintain thread safe access to ssh connections
    via an optional jump host. Enable shell commands,
    scp, and sftp operations.
    """

    def __init__(
        self,
        ip,
        port=22,
        username=None,
        password=None,
        prompt=None,
        private_key=None,
        timeout=None,
        use_ssh_agent=True,
        verbose_logs=False,
        sftp_enabled=True,
        using_jump_host=False,
        jump_host_public_ip=None,
        jump_host_private_ip=None,
        jump_host_username=None,
        jump_host_password=None,
        jump_host_port=None,
        jump_host_private_key=None,
    ):
        self.lock = threading.Lock()  # protects 'connections'
        self.connections = {}  # protected by lock
        self.ip = ip
        self.port = port
        self.username = username
        self.password = password
        self.prompt = prompt
        self.private_key = (
            paramiko.RSAKey.from_private_key(io.StringIO(private_key))
            if private_key
            else None
        )
        self.timeout = timeout
        self.use_ssh_agent = use_ssh_agent
        self.verbose_logs = verbose_logs
        self.sftp_enabled = sftp_enabled

        self.using_jump_host = using_jump_host
        self.jump_host_public_ip = jump_host_public_ip
        self.jump_host_private_ip = jump_host_private_ip
        if jump_host_private_ip is None:
            self.jump_host_private_ip = jump_host_public_ip
        self.jump_host_username = jump_host_username
        self.jump_host_password = jump_host_password
        self.jump_host_private_key = (
            paramiko.RSAKey.from_private_key(io.StringIO(jump_host_private_key))
            if jump_host_private_key
            else None
        )
        self.jump_host_port = int(jump_host_port) if jump_host_port else 22

    def _debug_log(self, s, thread_id):
        if self.verbose_logs:
            logger.info(f"{s} | thread {thread_id} | ip {self.ip}")

    def _info_log(self, s, thread_id):
        logger.info(f"{s} | thread {thread_id} | ip {self.ip}")

    def _get_state(self) -> Tuple[Any, State]:
        """Get the connection state of the calling thread"""
        state = None
        thread_id = threading.get_native_id()
        with self.lock:
            if thread_id not in self.connections:
                self.connections[thread_id] = State(thread_id, self.using_jump_host)
            state = self.connections[thread_id]
        return thread_id, state

    def _get_sock(self, ip, port, state) -> Union[paramiko.ProxyCommand, None]:
        """
        Return an open socket-like object in the form
        of a ParamikoCommand object (if necessary as defined by the conditions)
        """
        sock = None

        # For labs on internal corp netwrork, we should use fwdproxy_corp to connect
        # temproarily using justknobs to control the deployment (bunnylol jk ctf/fwdproxy_corp)
        if not constants.IS_EXTERNAL_DEPLOYMENT and justknobs.check(
            "ctf/fwdproxy_corp:use_fwdproxy_corp"
        ):

            command = f"fwdproxy_ssh_proxy --corp {ip} {port}"
            self._info_log(f"using {command} to connect.", state.thread_id)
            sock = paramiko.ProxyCommand(command)
        return sock

    def _create_tunnel(self, state) -> Any:
        """Create a tunnel through the jump host.
        Returns: a socket like object
        """
        if not self.using_jump_host:
            return self._get_sock(ip=self.ip, port=self.port, state=state)
        if state.connected:
            raise ConnectionError(f"thread {state.thread_id} opening multiple tunnels")

        self._info_log(
            f"Using JumpHost {self.jump_host_public_ip} {self.jump_host_port} to connect.",
            state.thread_id,
        )
        self._debug_log("_create_tunnel", state.thread_id)
        ssh_client = state.ssh_client_jump_host
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_client.connect(
            hostname=self.jump_host_public_ip,
            port=self.jump_host_port,
            username=self.jump_host_username,
            password=self.jump_host_password,
            timeout=self.timeout,
            allow_agent=self.use_ssh_agent,
            pkey=self.jump_host_private_key,
            sock=self._get_sock(
                ip=self.jump_host_public_ip, port=self.jump_host_port, state=state
            ),
        )
        # Create tunnel
        src_addr = (self.jump_host_private_ip, self.jump_host_port)
        dest_addr = (self.ip, self.port)
        transport = ssh_client.get_transport()
        return transport.open_channel("direct-tcpip", dest_addr, src_addr)

    def connect(self) -> None:
        """Connect to the ssh server"""
        thread_id, state = self._get_state()
        if state.connected:
            self._debug_log("connect | already connected", thread_id)
            return
        self._info_log("connect", thread_id)
        ssh_client = state.ssh_client
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_client.connect(
            hostname=self.ip,
            port=self.port,
            username=self.username,
            password=self.password,
            timeout=self.timeout,
            sock=self._create_tunnel(state),
            allow_agent=self.use_ssh_agent,
            pkey=self.private_key,
        )

        state.scp = SCPClient(ssh_client.get_transport())
        # TODO open sftp channel here once "sftp_enabled" is
        # integrated in the CTF server side. See also: sftp()
        # if self.sftp_enabled:
        #     state.sftp = paramiko.SFTPClient.from_transport(ssh_client.get_transport())
        state.connected = True

        with self.lock:
            self.connections[thread_id] = state

        self._info_log("connect | ok", thread_id)

    def disconnect(self) -> None:
        """Disconnect from the ssh server and jump host"""
        thread_id, state = self._get_state()
        self._info_log("disconnect", thread_id)

        if state.connected:
            state.connected = False
            if state.sftp is not None:
                state.sftp.close()
            if state.scp is not None:
                state.scp.close()
            state.ssh_client.close()
            if state.ssh_client_jump_host is not None:
                state.ssh_client_jump_host.close()
            self._debug_log("disconnect | ok", thread_id)
        else:
            self._debug_log("disconnect | not connected", thread_id)

        with self.lock:
            self.connections.pop(thread_id, None)

    def _read_stream(self, stream_name, stream):
        """Read all available data from stream"""
        rx = ""
        thread_id, state = self._get_state()
        if not state.connected:
            raise ConnectionError(f"read | not connected | thread {thread_id}")

        if stream_name == "stderr":
            ready_func = stream.channel.recv_stderr_ready
            recv_func = stream.channel.recv_stderr
        else:
            ready_func = stream.channel.recv_ready
            recv_func = stream.channel.recv

        while ready_func():
            chunk = recv_func(DEFAULT_READ_BYTES)
            if len(chunk) == 0:
                raise ConnectionError(f"read | channel closed | thread_id {thread_id}")
            rx += chunk.decode("utf-8", "ignore")
        return rx

    def _capture_std_stream_lines(
        self,
        stream_name,
        stream,
        stream_lines,
        stream_partial_line,
        on_stream_line_recv,
    ):
        had_data = False
        had_data_lines = False

        new_stream_data = self._read_stream(stream_name, stream)
        if new_stream_data:
            had_data = True
            lines = (stream_partial_line + new_stream_data).splitlines()
            stream_partial_line = ""
            if not new_stream_data.endswith(LF):
                stream_partial_line = lines.pop()
            for line in lines:
                if line and not line.isspace():
                    had_data_lines = True
                    if on_stream_line_recv:
                        on_stream_line_recv(line)
                    stream_lines.append(line)
        return (had_data, had_data_lines, stream_partial_line)

    def _read_std(  # noqa: C901
        self,
        timeout=DEFAULT_TIMEOUT_SECONDS,
        stdout_f=None,
        stderr_f=None,
        on_stdout_recv=None,
        on_stderr_recv=None,
        check_cancel=None,
        check_cancel_complete=None,
        check_return_code=False,
    ):
        """
        Read data from the stdout or stderr stream

        Poll multiple times a second for all available data

        Stop polling when:

        1. data was empty
            - this means SSH lib received an EOF and stream was closed
        2. canceled
            - STOP button on Test Results page in UI
        3. timeout
        4. "finished" message checking is enabled and "finished" message is received
            - CTF injects its own echos in between commands, to identify when they
              have completed
            - see: _wrap_cmd
        """

        # TODO stdout/stderr could be huge; replace with tmp file capture
        stdout_lines = deque()
        stderr_lines = deque()
        stdout_partial_line = ""
        stderr_partial_line = ""

        canceled = False
        done = False
        timed_out = False
        remaining_time = float(timeout)

        while not done and not timed_out:
            start_time = timer()

            if check_cancel and check_cancel():
                canceled = True
                break

            (
                had_stdout_data,
                had_stdout_data_lines,
                stdout_partial_line,
            ) = self._capture_std_stream_lines(
                stream_name="stdout",
                stream=stdout_f,
                stream_lines=stdout_lines,
                stream_partial_line=stdout_partial_line,
                on_stream_line_recv=on_stdout_recv,
            )

            (
                had_stderr_data,
                had_stderr_data_lines,
                stderr_partial_line,
            ) = self._capture_std_stream_lines(
                stream_name="stderr",
                stream=stderr_f,
                stream_lines=stderr_lines,
                stream_partial_line=stderr_partial_line,
                on_stream_line_recv=on_stderr_recv,
            )

            # check if end of expected output
            if had_stdout_data_lines:
                last = stdout_lines.pop()
                if last.rstrip(LF).endswith(CMD_END_MSG):
                    done = True
                else:
                    stdout_lines.append(last)

            elapsed_time = timer() - start_time
            if (
                not had_stdout_data
                and not had_stderr_data
                and elapsed_time < DEFAULT_POLL_DELAY_SECONDS
            ):
                time.sleep(DEFAULT_POLL_DELAY_SECONDS - elapsed_time)
                remaining_time -= DEFAULT_POLL_DELAY_SECONDS
            else:
                remaining_time -= elapsed_time
            timed_out = remaining_time <= 0

        returncode = 0
        if timed_out:
            message = f"CTF - timeout of {timeout} seconds reached while waiting for SSH command on Device."
            returncode = RC_TIMEOUT
            stdout_lines.append(LF)
            stdout_lines.append("---")
            stdout_lines.append(message)
            on_stdout_recv(message)
        elif canceled:
            # need to give graceful cancel some time to complete
            # no need for time elapsed level accuracy here
            done = False
            remaining_time = DEFAULT_TIMEOUT_CANCEL_SECONDS
            while not done:
                done = check_cancel_complete()
                if done:
                    break
                time.sleep(DEFAULT_POLL_DELAY_SECONDS)
                remaining_time -= DEFAULT_POLL_DELAY_SECONDS
                done = remaining_time <= 0

            returncode = RC_CANCEL
            stdout_lines.append(LF)
            stdout_lines.append("---")
            stdout_lines.append("CTF - canceled command")
        elif check_return_code and stdout_lines:
            last = stdout_lines.pop()
            rc = last.rstrip(LF)
            returncode = int(rc)

        return (LF.join(stdout_lines), LF.join(stderr_lines), returncode)

    def exec(
        self,
        cmd,
        timeout=DEFAULT_TIMEOUT_SECONDS,
    ):
        """Exec a shell command.. cannot cancel or capture output until done"""
        thread_id, state = self._get_state()
        if not state.connected:
            raise ConnectionError(f"exec | not connected | thread {thread_id}")
        self._debug_log(f"exec | cmd => {cmd}", thread_id)
        err = None
        in_cmd = cmd

        try:
            (_, stdout_f, stderr_f) = state.ssh_client.exec_command(
                cmd, timeout=timeout
            )
            stdout = deque()
            stderr = deque()
            for line in stdout_f.readlines():
                if line and not line.isspace():
                    stdout.append(line)
            for line in stderr_f.readlines():
                if line and not line.isspace():
                    stderr.append(line)

            returncode = stdout_f.channel.recv_exit_status()

        except socket.timeout as e:
            err = f"send failed | cmd => {in_cmd} | thread => {thread_id} | socket.timeout => {str(e)}"
        except socket.error as e:
            err = f"send failed | cmd => {in_cmd} | thread => {thread_id} | socket.error => {str(e)}"

        if err is not None:
            raise ConnectionError(err)

        return (LF.join(stdout), LF.join(stderr), returncode)

    @staticmethod
    def _wrap_cmd(
        cmd,
        ensure_newline=False,
        check_returncode_cmd=None,
    ):
        if ensure_newline:
            cmd += " && echo ''"
        if check_returncode_cmd:
            cmd += f" ; {check_returncode_cmd}"
        cmd += f" ; echo {CMD_END_MSG}{LF}"

        return cmd

    def send(  # noqa: C901
        self,
        cmd,
        shell_family_name,
        shell_name,
        timeout=DEFAULT_TIMEOUT_SECONDS,
        on_process_start=None,
        on_process_stop=None,
        on_stdin_send=None,
        on_stdout_recv=None,
        on_stderr_recv=None,
        check_cancel=None,
        check_cancel_complete=None,
    ):
        """Send a shell command"""
        thread_id, state = self._get_state()
        if not state.connected:
            raise ConnectionError(f"send | not connected | thread {thread_id}")
        self._debug_log(f"send | cmd => {cmd}", thread_id)
        err = None
        in_cmd = cmd

        try:
            pid = None

            (stdin_f, stdout_f, stderr_f) = state.ssh_client.exec_command(
                SHELL_BLOCKING_CMD_SWITCHER.get(shell_name),
                timeout=timeout,
            )

            pid_cmd = self._wrap_cmd(SHELL_PID_CMD_SWITCHER.get(shell_family_name))

            stdin_f.write(pid_cmd)
            stdin_f.flush()

            if on_stdin_send:
                for line in pid_cmd.splitlines():
                    if line and not line.isspace():
                        on_stdin_send(line)

            (pid, _, __) = self._read_std(
                timeout=timeout,
                stdout_f=stdout_f,
                stderr_f=stderr_f,
                on_stdout_recv=on_stdout_recv,
                on_stderr_recv=on_stderr_recv,
            )

            if on_process_start and pid.isdigit():
                on_process_start(pid)

            full_cmd = self._wrap_cmd(
                cmd,
                ensure_newline=True,
                check_returncode_cmd=SHELL_RC_CMD_SWITCHER.get(shell_family_name),
            )

            stdin_f.write(full_cmd)
            stdin_f.flush()

            if on_stdin_send:
                for line in full_cmd.splitlines():
                    if line and not line.isspace():
                        on_stdin_send(line)

            (stdout, stderr, returncode) = self._read_std(
                timeout=timeout,
                stdout_f=stdout_f,
                stderr_f=stderr_f,
                on_stdout_recv=on_stdout_recv,
                on_stderr_recv=on_stderr_recv,
                check_cancel=check_cancel,
                check_cancel_complete=check_cancel_complete,
                check_return_code=True,
            )

            if returncode != RC_CANCEL:
                if on_process_stop and pid.isdigit():
                    on_process_stop(pid)

        except socket.timeout as e:
            err = f"send failed | cmd => {in_cmd} | thread => {thread_id} | socket.timeout => {str(e)}"
        except socket.error as e:
            err = f"send failed | cmd => {in_cmd} | thread => {thread_id} | socket.error => {str(e)}"

        if err is not None:
            raise ConnectionError(err)

        return (stdout, stderr, returncode)

    def sftp(self, op, path, local_path=""):
        """Execute an sftp command"""
        thread_id, state = self._get_state()
        if not self.sftp_enabled:
            raise RuntimeError(
                f"sftp {op} | disabled | path => {path} | local_path => {local_path} | thread {thread_id}"
            )
        if not state.connected:
            raise ConnectionError(
                f"sftp {op} | path => {path} | local_path => {local_path} | thread => {thread_id} not connected"
            )

        # TODO Remove. See connect()
        if state.sftp is None:
            state.sftp = paramiko.SFTPClient.from_transport(
                state.ssh_client.get_transport()
            )
            with self.lock:
                self.connections[thread_id] = state

        self._debug_log(
            f'sftp {op} | path "{path}" | local_path "{local_path}"', thread_id
        )
        ret = None
        if op == "listdir_attr":
            ret = state.sftp.listdir_attr(path=path)
        elif op == "listdir":
            ret = state.sftp.listdir(path=path)
        elif op == "get":
            state.sftp.get(remotepath=path, localpath=local_path)
        elif op == "stat":
            ret = state.sftp.stat(path=path)
        elif op == "mkdir":
            state.sftp.mkdir(path=path)
        elif op == "remove":
            state.sftp.remove(path=path)
        elif op == "rmdir":
            state.sftp.rmdir(path=path)
        else:
            raise ValueError(f"Unknown sftp operation {op}")
        return ret

    def scp(self, op, local_path, remote_path, recursive=False):
        """Execute an scp command"""
        thread_id, state = self._get_state()
        if not state.connected:
            raise ConnectionError(
                f'scp {op} | local_path "{local_path}" | remote_path "{remote_path}" | recursive {recursive} | thread {thread_id} not connected'
            )

        self._debug_log(
            f'scp {op} | local_path "{local_path}" | remote_path "{remote_path}" | recursive {recursive}',
            thread_id,
        )

        ret = None
        if op == "put":
            ret = state.scp.put(
                files=local_path, remote_path=remote_path, recursive=recursive
            )
        elif op == "get":
            ret = state.scp.get(
                local_path=local_path,
                remote_path=remote_path,
                recursive=recursive,
                preserve_times=True,
            )
        elif op == "get_glob":
            with SCPClient(
                state.ssh_client.get_transport(), sanitize=lambda x: x
            ) as scp:
                scp.get(remote_path=remote_path, local_path=local_path)
        else:
            raise ValueError(f"Unknown sftp operation {op}")
        return ret
