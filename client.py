#!/usr/bin/env python3
from os import system
from paramiko import SSHClient, AutoAddPolicy, RSAKey
from paramiko.auth_handler import AuthenticationException, SSHException
from scp import SCPClient, SCPException
from log import logger


class RemoteClient:
    """Client to interact with a remote host via SSH & SCP.

    Code from https://github.com/hackersandslackers/paramiko-tutorial

    """
    def __init__(self, host, user, ssh_key_filepath, remote_path):
        self.host = host
        self.user = user
        self.ssh_key_filepath = ssh_key_filepath
        self.remote_path = remote_path
        self.client = None
        self.scp = None
        self.conn = None
        # self._upload_ssh_key(self)

    @logger.catch
    def __get_ssh_key(self):
        """Fetch locally stored SSH key."""
        try:
            self.ssh_key = RSAKey.from_private_key_file(self.ssh_key_filepath)
            logger.info(f'Found SSH key at self {self.ssh_key_filepath}')
        except SSHException as error:
            logger.error(error)
        return self.ssh_key

    @logger.catch
    def __upload_ssh_key(self):
        try:
            system(f'ssh-copy-id -i {self.ssh_key_filepath} {self.user}@{self.host}>/dev/null 2>&1')
            system(f'ssh-copy-id -i {self.ssh_key_filepath}.pub {self.user}@{self.host}>/dev/null 2>&1')
            logger.info(f'{self.ssh_key_filepath} uploaded to {self.host}')
        except FileNotFoundError as error:
            logger.error(error)

    def __connect(self):
        """Open a connection to the remote host."""
        if self.conn is None:
            try:
                self.client = SSHClient()
                self.client.load_system_host_keys()
                self.client.set_missing_host_key_policy(AutoAddPolicy())
                self.client.connect(
                    self.host,
                    username=self.user,
                    key_filename=self.ssh_key_filepath,
                    look_for_keys=True,
                    timeout=5000
                )
                self.scp = SCPClient(self.client.get_transport())
            except AuthenticationException as error:
                logger.error(f'Authentication failed: did you remember to create a key? {error}')
                raise error
        return self.client

    def disconnect(self):
        """Close the connections"""
        if self.client:
            self.client.close()
        if self.scp:
            self.scp.close()

    @logger.catch
    def bulk_upload(self, file_list):
        """Upload mutiple files to a remote directory

        :param file_list: List of local files to be uploaded.
        :type file_list: List[str]
        """
        self.conn = self.__connect()
        uploads = [self.__upload_single_file(fn) for fn in file_list]
        logger.info(f'Finished uploading {len(uploads)} files to {self.remote_path} on {self.host}')

    def __upload_single_file(self, fn):
        """Upload a single file to a remote directory"""
        upload = None
        try:
            self.scp.put(
                fn,
                recursive=True,
                remote_path=self.remote_path
            )
            upload = fn
        except SCPException as error:
            logger.error(error)
            raise error
        finally:
            logger.info(f'Uploaded {fn} to {self.remote_path}')
            return upload

    def download_file(self, file):
        """Download file from remote host."""
        self.conn = self.__connect()
        self.scp.get(file)

    @logger.catch
    def execute_commands(self, commands):
        """Execute multiple commands in succession.

        :param commands: List of unix commands as strings.
        :type commands: List[str]
        """
        self.conn = self.__connect()
        for cmd in commands:
            stdin, stdout, stderr = self.client.exec_command(cmd)
            stdout.channel.recv_exit_status()
            response = stdout.readlines()
            for line in response:
                logger.info(f'INPUT: {cmd} | OUTPUT: {line}')

    @logger.catch
    def execute_single_command(self, command):
        """Execute a command and return the result from STDOUT

        :param command: A unix command as a string
        :type command: str
        """
        self.conn = self.__connect()
        stdin, stdout, stderr = self.client.exec_command(command)
        stdout.channel.recv_exit_status()
        errors = stderr.readlines()
        if len(errors) > 0:
            error_msg = "\n".join(errors)
            logger.error(f"Command failed: {error_msg}")
            raise Exception("SSH Remote Command failed, see log")
        response = stdout.readlines()
        return response
