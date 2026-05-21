import socket
import traceback
from threading import Thread

from paramiko import SSHException

from attacks.scripts.base_attack import BaseAttack
from defs.remote import Remote
from defs.std_streams import StdStreams
from defs.utils import log
from defs.config import Config as Cfg

# Location of the file to send to the remote device
FILE_TO_SEND = "code/attacks/files/password_guess.py"


class PasswordGuessAttack(BaseAttack):
	"""
	Attack that sends a script that tries to crack a password through brute force to the remote device and runs it there
	"""

	remote: Remote
	active: bool
	streams: StdStreams

	def __init__(self):
		self.active = False

	def get_attack_name(self) -> str:
		return "Password"

	def is_synchronous(self) -> bool:
		return False

	def start(self, device_num: int) -> bool:
		try:
			self.remote = Remote.connect_end_device(device_num)
		except (SSHException, TimeoutError, socket.timeout, socket.error):
			log("Error: Couldn't connect to a remote device to run the password guessing attack. Full exception:")
			print(traceback.format_exc())
			return False

		self.remote.cd("~")

		self.remote.send_file(FILE_TO_SEND, Cfg.get().pass_remote_file)

		self.active = True
		self.streams = self.remote.exec_command_async(Cfg.get().remote_python_command + " " + Cfg.get().pass_remote_file)

		# Use a separate thread to check for errors once the script exits
		Thread(target=self._check_exit, args=[self.streams]).start()

		return True

	def end(self):
		if self.active:
			# Close the channel. Since exec_command_async creates a virtual terminal, this kills said terminal too,
			# which immediately stops the password guessing program.
			self.remote.close()
			self.active = False
