#!/usr/bin/python3
from abc import ABCMeta
import paramiko
import os
import time
import re
import logging
import traceback

from scp import SCPClient
from datetime import datetime, timedelta
from paramiko_expect import SSHClientInteraction
from paramiko.ssh_exception import SSHException

log = logging.getLogger('Diag')

class SSHBase(metaclass=ABCMeta):
    def __init__(self, host=None, port=22, username=None, password=None, pkey_path=None, timeout=10):
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.pkey_path = pkey_path
        self.timeout = timeout  # connection timeout

        self.sudo_en = False
        self.sudo_pass = "ubnt"

        self._last_progress_msg = None

    def enable_sudo(self, sudo_pass = "ubnt"):
        self.sudo_en = True
        self.set_sudo_pass(sudo_pass)

    def disable_sudo(self):
        self.sudo_en = False
        self.sudo_pass = None

    def set_sudo_pass(self, sudo_pass):
        self.sudo_pass = sudo_pass

    def connect(self, host=None, timeout=10):
        if host is not None:
            self.host = host

        self.timeout = timeout
        if self.password is not None:
            self.client.connect(hostname=self.host, port=self.port, username=self.username, password=self.password, timeout=self.timeout)
        elif self.pkey_path is not None:
            self.pkey = paramiko.RSAKey.from_private_key_file(self.pkey_path)
            self.client.connect(hostname=self.host, username=self.username, port=self.port, pkey=self.pkey, timeout=self.timeout)

    def polling_connect(self, mins=5, throw_exception=False):
        """retry connecting in a period of time
        Arguments:
            timeout[int]
        Returns: True / False if throw_exception is False
        """
        print("Polling connecting to " + self.host)
        polling_time = datetime.now() + timedelta(minutes=mins)
        is_connect = False
        ex = Exception()
        while datetime.now() < polling_time:
            try:
                self.connect()
                is_connect = True
                break
            except Exception as e:
                time.sleep(5)
                ex = e
                print(str(ex))

        if not is_connect:
            if throw_exception:
                raise ex
            else:
                print(str(ex))
                return False
        return True

    def _progress4(self, filename, size, sent, peername):
        msg = "({}:{}) {}'s progress: {}%".format(
            peername[0], peername[1], filename, int(float(sent)/float(size)*100))

        if self._last_progress_msg != msg:
            log.info(msg)
            self._last_progress_msg = msg

    '''
        To view from the FCD host.
        FCD host(local) put file to DUT(remote)
    '''
    def put_file(self, local, remote, log_progess_en=False):
        # only check if local is file only when local type is string only
        if type(local) is str and os.path.isfile(local) is False:
            log.debug('"{}" is not a file'.format(local))
            return
        progress = self._progress4 if log_progess_en else None
        scp_obj = SCPClient(self.client.get_transport(), progress4=progress)
        scp_obj.put(files=local, remote_path=remote)

    '''
        To view from the FCD host.
        FCD host(local) get file to DUT(remote)
    '''
    def get_file(self, remote, local, log_progess_en=False):
        progress = self._progress4 if log_progess_en else None
        scp_obj = SCPClient(self.client.get_transport(), progress4=progress)
        scp_obj.get(local_path=local, remote_path=remote)

    def close(self):
        self.client.close()


class SSHClient(SSHBase):
    def __init__(self, host=None, port=22, username=None, password=None, pkey_path=None, timeout=10, polling_connect=False, polling_mins=5, e_except=False):
        super(SSHClient, self).__init__(host, port, username, password, pkey_path, timeout)
        self.e_except = e_except
        if not polling_connect:
            self.connect()
        else:
            self.polling_connect(mins=polling_mins, throw_exception=True)
        log.info("{} uptime: {}".format(self.host, self.execmd_getmsg("cat /proc/uptime").strip("\n")))

    def execmd(self, cmd, timeout=None, get_exit_val=True, sudo_en=None, e_except=None):
        return self._exec_command(cmd=cmd, timeout=timeout, get_exit_val=get_exit_val,
                                  e_except=self.e_except if e_except is None else e_except,
                                  sudo_en=self.sudo_en if sudo_en is None else sudo_en)

    def execmd_getmsg(self, cmd, stderr=False, get_all=False, timeout=None, sudo_en=None, decode_en=True, e_except=True, log_en=True):
        return self._exec_command(cmd=cmd, get_stdout=True, get_stderr=stderr, get_all=get_all,
                                  timeout=timeout, e_except=self.e_except,
                                  sudo_en=self.sudo_en if sudo_en is None else sudo_en, decode_en=decode_en,
                                  log_en=log_en)

    def execmd_expect(self, cmd, expectmsg, stderr=False, timeout=None):
        msg = self.execmd_getmsg(cmd=cmd, stderr=stderr, timeout=timeout)
        if expectmsg in msg:
            return True
        else:
            return False

    def execmd_expect_get_index(self, cmd, expectmsg, stderr=False, timeout=None):
        """This API is mostly like the expect_get_index() in the expect_tty.py
        """
        msg = self.execmd_getmsg(cmd=cmd, stderr=stderr, timeout=timeout)
        num_msg = len(expectmsg)
        for i in range(num_msg):
            if expectmsg[i] in msg:
                return i
            else:
                if i == num_msg-1:
                    return -1

    def exec_command_get_pty(self, cmd):
        stdin, stdout, stderr = self.client.exec_command(command=cmd, get_pty=True)
        return stdin, stdout, stderr

    def execmd_interact(self, cmd, interact, stderr=False, timeout=None):
        try:
            stdin, stdout, stderror = self.client.exec_command(command=cmd, timeout=timeout, get_pty=True)
        except Exception as e:
            print(str(e))
            return -1

        num_act = len(interact)
        tnum = timeout/0.25
        ct = 0
        ctt = 0
        while stdout.channel.recv_ready() and ct < num_act and ctt < tnum:
            bf = stdout.readline()
            print(bf)
            if interact[ct][0] in bf:
                stdin.write(interact[ct][1] + "\n")
                stdin.flush()
                ct += 1

            time.sleep(0.25)

    def _exec_command(self, cmd, get_stdout=False, get_stderr=False, get_all=False, timeout=None, get_exit_val=True,
                      e_except=False, sudo_en=False, decode_en=True, log_en=True):
        """exec command and get output/exit code

        Arguments:
            cmd {[str]} -- [cmd]

        Keyword Arguments:
            timeout {int} -- timeout of cmd, if exceeds, paramiko will throw exception
            get_stdout {bool}
            get_stderr {bool}
            get_all {bool}      - get both stdin, stdout, stderr
            get_exit_val {bool} - whether get exit code. If it's "True", waits the exit val at most 180 seconds and
                                  raise a SSHException. If it's "False", returns None immediately
            e_except {bool}     - raise exception when exit code is not equal zero.
                                  This option only affects when get_exit_val is True
            sudo_en {bool}      - if prefix "sudo" at string head and write password after issuing the cmd

        Returns:
            stdout [str] or exit code or all std related stuffes
        """
        cmd = "sudo {}".format(cmd) if sudo_en is True else cmd
        if log_en is True:
            log.debug('[ssh cmd, {}] {}'.format(self.host, cmd))
        try:
            if self.client.get_transport().is_active() is False:
                log.error("The session {} ({}) is not active".format(self, self.host))

            stdin, stdout, stderror = self.client.exec_command(command=cmd, timeout=timeout,
                                                               get_pty=True if sudo_en is True else False)
            if sudo_en is True:
                time.sleep(0.1)
                stdin.write("{}\n".format(self.sudo_pass))
                stdin.flush()
        except Exception as e:
            print(str(e))
            return -1

        if get_stderr is True:
            return stdout.read().decode(), stderror.read().decode()
        elif get_all is True:
            return stdin, stdout.read().decode(), stderror.read().decode()
        elif get_stdout is True:
            if decode_en == False:
                return stdout.read().decode('utf-8', 'ignore')
            return stdout.read().decode()

        # Do not change the in-order of conditional expressions at will unless you know what you are doing.
        elif get_exit_val is True:
            seconds = timeout if timeout is not None else 180
            polling_time = datetime.now() + timedelta(seconds=seconds)
            while datetime.now() < polling_time:
                if stdout.channel.exit_status_ready() is True:
                    exit_status = stdout.channel.recv_exit_status()
                    break
                else:
                    time.sleep(0.1)
            else:
                raise SSHException("cmd:\"{}\" timeout, can't get exit code".format(cmd))

            # The case that the return value is not equal zero
            if exit_status != 0:
                if e_except is True:
                    raise SSHException("Cmd: \"{}\", Exit code: {}, Stderr message: \"{}\"".format(cmd,
                                        exit_status, stderror.read().decode().strip()))
                else:
                    log.debug("Cmd: \"{}\", Exit code: {}, Stderr message: \"{}\"".format(cmd,
                              exit_status, stderror.read().decode().strip()))
            return exit_status
        return None

    def dut_isfile(self, path):
        basename = os.path.basename(path)
        rt = self.execmd_expect("ls -la " + path, basename)
        return rt

    def put_file_retry(self, local, remote, retry_time=3, interval=5):

        is_pass = False
        cur_time = 0
        while True:
            try:
                cur_time += 1
                self.put_file(local=local, remote=remote, log_progess_en=True)
            except Exception as e:
                log.error(traceback.format_exc())
                log.error(str(e))
                if cur_time == retry_time:
                    break
                log.info('Keeping retry, Have tried {} time..'.format(cur_time))
                time.sleep(interval)
            else:
                log.info('[pass] put_file_retry, Have tried {} time..'.format(cur_time))
                is_pass = True
                break

        if not is_pass:
            msg = '[fail] Stop keeping retry, Have tried {} time'.format(cur_time)
            log.error(msg)
            raise Exception(msg)


class SSHExpect(SSHBase):
    def __init__(self, host=None, port=22, username=None, password=None, pkey_path=None, timeout=10,
                 display=True, output_callback=None):
        super(SSHExpect, self).__init__(host, port, username, password, pkey_path, timeout)
        self.lnxpmt = ""
        self.shpmt = ""

        self.connect()
        if output_callback is None:
            self.interact = SSHClientInteraction(self.client, timeout=timeout, newline='\n', display=display)
        else:
            self.interact = SSHClientInteraction(self.client, timeout=timeout, newline='\n', display=display,
                                                 output_callback = output_callback)

    def expect_action(self, timeout, action, post_exp=None, pre_n=True, pos_n=False):
        """Expect and send action cmd.
            Will raise ExceptionPexpect if expect timeout
            exit if expect come accross EOF
        """
        index = 0
        prompts = [
            self.lnxpmt,
            self.shpmt
        ]
        if post_exp is not None:
            prompts.append(post_exp)

        if pre_n is True:
            self.interact.send("")
            index = self.interact.expect(prompts, timeout)
            self.interact.current_output_clean

        if index >= 0:
            self.interact.send(action)
            if pos_n is True:
                self.interact.send("")
            self.interact.expect(prompts, timeout)
            self.interact.current_output_clean

    def expect_get_output(self, timeout, action, post_exp=None, pre_n=True, pos_n=False):
        """Expect and send action cmd.
            Will raise ExceptionPexpect if expect timeout
            exit if expect come accross EOF
        """
        index = 0
        prompts = [
            self.lnxpmt,
            self.shpmt
        ]
        if post_exp is not None:
            prompts.append(post_exp)

        if pre_n is True:
            self.interact.send("")
            index = self.interact.expect(prompts, timeout)
            self.interact.current_output_clean

        if index >= 0:
            self.interact.send(action)
            if pos_n is True:
                self.interact.send("")
            self.interact.expect(prompts, timeout)
            return self.interact.current_output_clean

    def expect_get_output2(self, timeout, action):
        """Expect the previous prompt first and send a newline to keep a prompt in buffer"""
        default_match_prefix = ".*"
        prompts = [self.lnxpmt, self.shpmt]
        self.interact.expect(prompts, timeout, default_match_prefix = default_match_prefix)
        self.interact.send(action)
        self.interact.expect(prompts, timeout, default_match_prefix = default_match_prefix)
        self.interact.send("")
        return self.interact.current_output_clean

    def expect_action2(self, timeout, pre_expect, action, post_expect):
        """Expect the previous prompt first and send a newline to keep a prompt in buffer"""
        default_match_prefix = ".*"
        self.interact.expect(pre_expect+".*", timeout, default_match_prefix = default_match_prefix)
        self.interact.send(action)
        self.interact.expect(post_expect+".*", timeout, default_match_prefix = default_match_prefix)
        self.interact.send("")
        return self.interact.current_output_clean


    def expect_get_index(self, timeout, action, post_exp=None, pre_n=True, pos_n=False):
        """Expect and send action cmd.
            Will raise ExceptionPexpect if expect timeout
            exit if expect come accross EOF
        """
        index = 0
        rt = -1
        prompts = [
            self.lnxpmt,
            self.shpmt
        ]
        if post_exp is not None:
            prompts.append(post_exp)

        if pre_n is True:
            self.interact.send("")
            index = self.interact.expect(prompts, timeout)
            self.interact.current_output_clean

        if index >= 0:
            self.interact.send(action)
            self.interact.send("")
            rt = self.interact.expect(prompts, timeout)
            self.interact.current_output_clean

        return rt


class SSHOperation(SSHBase):
    def __init__(self, role='DUT', host=None, port=22, username=None, password=None, pkey_path=None, timeout=10, display=True):
        super(SSHOperation, self).__init__(host, port, username, password, pkey_path, timeout)
        self.connect()
        self.interact = SSHClientInteraction(self.client, timeout=10, newline='\n', display=display)

        self.__cmd_log = ''
        self.__cmd_list = []
        self.__role = role
        SSHOperation.__status = 'run'

    @property
    def log(self):
        return self.__cmd_log

    @property
    def command(self):
        return str( 'command history: ' + ' -> '.join(self.__cmd_list) )

    @property
    def status(self):
        return SSHOperation.__status

    def wait(self, timeout=5, string=''):
        if SSHOperation.__status == 'run':
            self.__cmd_list.append('wait({},"{}")'.format(timeout, string))
            try:
                self.interact.expect(string + '.*', timeout, default_match_prefix=".*")
                self.__cmd_log += self.interact.current_output
            except :
                self.__cmd_log += self.interact.current_output
                self.__cmd_log += '\n{}\nError: fail to wait({},"{}")\n{}\n'.format(100 * '-', timeout, string, 100 * '-')
                SSHOperation.__status = 'stop'
                raise Exception()


    def check(self, timeout=5, keyword=''):
        if SSHOperation.__status == 'run':
            time.sleep(0.5)
            self.__cmd_list.append('check({},"{}")'.format(timeout, keyword))
            try :
                index = None
                if isinstance(keyword, list):
                    keyword = [s + '.*' for s in keyword]
                else:
                    keyword += '.*'
                index = self.interact.expect(keyword , timeout, default_match_prefix=".*")
                self.__cmd_log += self.interact.current_output
            except :
                self.__cmd_log += self.interact.current_output

            return index

    def send(self, action):
        if SSHOperation.__status == 'run':
            self.__cmd_list.append('send("{}")'.format(action))
            self.interact.send(action)

    def onlysend(self, action):
        if SSHOperation.__status == 'run':
            self.__cmd_list.append('onlysend("{}")'.format(action))
            self.interact.send(action, newline='')

    def sleep(self, sec=2):
        if SSHOperation.__status == 'run':
            self.__cmd_list.append('sleep({})'.format(sec))
            time.sleep(sec)

    def parse(self, pattern='.*'):
        if SSHOperation.__status == 'run':
            self.__cmd_list.append('parse("{}")'.format(pattern))
            ParserResult = ''

            for match in re.finditer(pattern, self.__cmd_log , re.IGNORECASE):
                ParserResult = match.groups()
            ParserResult = ''.join(ParserResult)

            if ParserResult == '':
                self.__cmd_log += '\n{}\nError: fail to parse("{}")\n{}\n'.format(100 * '-', pattern, 100 * '-')
                SSHOperation.__status = 'stop'

            return str(ParserResult)
