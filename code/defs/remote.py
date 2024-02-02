import os
import socket
import time

import paramiko
from paramiko import SFTPClient, SSHException
from paramiko.client import SSHClient

from defs.config import Config as Cfg
from defs.std_streams import StdStreams
from defs.utils import log


class Remote:
	"""
	Class used to perform remote operations on a different device, such as file transfers or executing remote files
	"""

	server: str
	port: int
	user: str
	password: str

	ssh: SSHClient
	sftp: SFTPClient

	def __init__(self, server: str, port: int, user: str, password: str):
		self.server = server
		self.port = port
		self.user = user
		self.password = password

		# Stop Paramiko from printing exceptions to the console. We'll catch them and deal with them if required.
		# noinspection PyUnresolvedReferences
		paramiko.util.log_to_file(os.devnull)

		# Create SSH client
		self.ssh = paramiko.SSHClient()
		self.ssh.load_system_host_keys()
		self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
		self.ssh.connect(server, port, user, password, timeout=Cfg.get().connection_timeout)

		# Create SFTP client
		self.sftp = self.ssh.open_sftp()

	@staticmethod
	def get_ip(device_num: int) -> str:
		"""
		Returns the IP address of a device given its ID
		"""
		return str(Cfg.get().device_conn_data[device_num - 1][0])

	@staticmethod
	def get_username(device_num: int) -> str:
		"""
		Returns the IP address of a device given its ID
		"""
		return str(Cfg.get().device_conn_data[device_num - 1][1])

	@classmethod
	def connect_end_device(cls, device_num: int):
		"""
		Connects to one of the end devices given its device number
		"""
		entry = Cfg.get().device_conn_data[device_num - 1]

		tries = Cfg.get().max_connection_tries
		while True:
			try:
				return cls(entry[0], 22, entry[1], entry[2])
			except (SSHException, TimeoutError, socket.timeout, socket.error) as e:
				tries -= 1
				if tries > 0:
					log("Warning: Failed to estabilish SSH connection to device " + str(device_num) + ". Attempts "
						"left: " + str(tries) + ".")
					if e is SSHException:
						time.sleep(0.5)
				else:
					raise

	def cd(self, path: str):
		"""
		Changes active directory, both for executing commands and for transfering files.
		"""
		# sftp.chdir() doesn't seem to support "~"
		path = path.replace("~", self.get_home_folder())
		self.exec_command_sync("cd " + path)
		self.sftp.chdir(path)

	def mkdir(self, path: str):
		"""
		Creates a directory in the remote device. No error is thrown if the directory already exists.
		"""
		try:
			self.sftp.mkdir(path)
		except OSError:
			pass

	def send_file(self, local_file: str, remote_file: str):
		"""
		Sends a file to the remote device. If the containing directory doesn't exist, it will be created.
		local_file: Path to the local file that will be sent
		remote_file: Path to the remote file that will be created or overwritten
		"""
		remote_dir = os.path.dirname(remote_file)
		self.mkdir(remote_dir)
		self.sftp.put(local_file, remote_file)

	def exec_command_sync(self, command: str) -> StdStreams:
		"""
		Executes a command synchronously. Returns the opened streams.
		"""
		streams = StdStreams(self.ssh.exec_command(command))
		streams.stdout.channel.recv_exit_status()  # Blocking call
		return streams

	def exec_command_async(self, command: str) -> StdStreams:
		"""
		Executes a command asynchronously. Returns the opened streams.
		A virtual terminal is created when running the command, which allows performing some operations (like
		killing the terminal to end the remote-running process)
		"""
		return StdStreams(self.ssh.exec_command(command, get_pty=True))

	def get_home_folder(self) -> str:
		"""
		Returns the absolute path to the home folder of the current user
		"""
		return "/home/" + self.user

	def close(self):
		self.sftp.close()
		self.ssh.close()
