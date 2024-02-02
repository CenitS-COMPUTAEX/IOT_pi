import socket
import time
import traceback
from enum import Enum
from threading import Thread

from paramiko import SSHException

from attacks.attack_type import AttackType
from attacks.scripts.base_attack import BaseAttack
from defs.remote import Remote
from defs.utils import log
from defs.config import Config as Cfg


# Used by the loop thread to signal whether the attack was started successfully or not
class EncryptionStartStatus(Enum):
	INIT = 0,
	STARTING = 1,
	SUCCESS = 2,
	FAILURE = 3


class EncryptionAttack(BaseAttack):
	"""
	Attack that sends an encryption program to the target device and runs it there, encrypting all the
	files under a test directory.
	"""

	remote: Remote
	device_num: int
	active: bool
	stop_flag: bool
	start_status: EncryptionStartStatus

	def __init__(self):
		self.active = False
		self.stop_flag = False
		self.start_status = EncryptionStartStatus.INIT

	def get_attack_name(self) -> str:
		return "Encryption"

	def is_synchronous(self) -> bool:
		return False

	def start(self, device_num: int) -> bool:
		self.device_num = device_num
		try:
			self.remote = Remote.connect_end_device(device_num)
		except (SSHException, TimeoutError, socket.timeout, socket.error):
			log("Error: Couldn't connect to a remote device to run the encryption attack. Full exception:")
			print(traceback.format_exc())
			self.active = False
			return False
		self.remote.cd("~")

		self.remote.send_file(Cfg.get().get_file_to_send(AttackType.ENCRYPTION, device_num),
			Cfg.get().encryption_remote_file)
		self.remote.sftp.chmod(Cfg.get().encryption_remote_file, 0o755)

		self.stop_flag = False
		self.active = True

		self.remote.close()

		self.start_status = EncryptionStartStatus.STARTING
		Thread(target=self.loop).start()
		while self.start_status == EncryptionStartStatus.STARTING:
			# Wait until we know if the attack was started successfully
			time.sleep(0.1)
		return self.start_status == EncryptionStartStatus.SUCCESS

	def loop(self):
		"""
		Calls the sent encryption script until the stop flag is set.
		Meant to be run in a separate thread.
		"""
		try:
			# Remote must be re-instantiated for SSH calls to work
			remote = Remote.connect_end_device(self.device_num)
			# Signal that the attack was successfully started
			self.start_status = EncryptionStartStatus.SUCCESS
			while not self.stop_flag:
				# Run sent file and wait until it ends
				streams = remote.exec_command_sync("./" + Cfg.get().encryption_remote_file + " " +
					Cfg.get().encryption_folder_to_encrypt + " " + str(Cfg.get().encryption_min_duration))

				# Ensure that the program exited successfully
				exit_code = streams.stdout.channel.recv_exit_status()
				if exit_code != 0:
					self._print_remote_error(exit_code, streams)
					# Stop early
					self.stop_flag = True
			remote.close()
		except SSHException:
			log("Error: Couldn't connect to a remote device to run the encryption attack. Full exception:")
			print(traceback.format_exc())
			# Signal that the attack couldn't be started
			self.start_status = EncryptionStartStatus.FAILURE
		self.active = False

	def end(self):
		self.stop_flag = True
		# Wait until the current iteration of the script ends
		log("Waiting for encryption script to finish...")
		time_start = time.time()
		while self.active:
			if time.time() - time_start < Cfg.get().encryption_wait_timeout:
				time.sleep(0.1)
			else:
				# This probably leaks the thread used for the connection, but it's better than a hang.
				log("Warning: Timeout expired while waiting for encryption attack to end. Continuing anyway.")
				break
