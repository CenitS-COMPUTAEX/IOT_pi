import signal
from subprocess import Popen, PIPE, STDOUT

from attacks.scripts.base_attack import BaseAttack
from defs.remote import Remote
from defs.utils import log
from defs.config import Config as Cfg


class FloodAttack(BaseAttack):
	"""
	Attack that floods the target with TCP SYN requests.
	"""

	# Subprocess created to run the attack tool
	subprocess: Popen

	def get_attack_name(self) -> str:
		return "Flood"

	def is_synchronous(self) -> bool:
		return False

	def start(self, device_num: int) -> bool:
		input_sequence = self._get_command(device_num).split(" ")
		self.subprocess = Popen(input_sequence, stdout=PIPE, stderr=STDOUT)
		return True

	def end(self):
		self.subprocess.send_signal(signal.SIGINT)
		log("Waiting for flood attack script to finish...")
		stdout, _ = self.subprocess.communicate()
		if self.subprocess.returncode != 0:
			log("Warning: Flood attack exited with status " + str(self.subprocess.returncode) + ".\n" +
				"Program output: ")
			print(stdout.decode("utf-8"))

	def _get_command(self, device_num: int) -> str:
		"""
		Returns The command string that should be run to launch the attack executable on a given device
		device_id: Number of the device the attack will be launched against
		"""
		return "./" + Cfg.get().flood_executable_file + " " + Remote.get_ip(device_num) + " -f " + \
			str(Cfg.get().flood_delay_micro)
