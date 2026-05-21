from defs.exceptions import IllegalOperationError
from attacks.scripts.base_attack import BaseAttack
from defs.remote import Remote
from defs.utils import log
from defs.config import Config as Cfg

# Location of the file to send to the remote device
FILE_TO_SEND = "code/attacks/files/test.py"
# Destination file in the remote
REMOTE_FILE = "files/test.py"


class TestAttack(BaseAttack):

	remote: Remote
	active: bool

	def __init__(self):
		self.active = False

	def get_attack_name(self) -> str:
		return "Test"

	def is_synchronous(self) -> bool:
		return True

	def start(self, device_num: int):
		# Try connecting to the end device, sending a test file and executing it
		self.remote = Remote.connect_end_device(device_num)
		self.remote.cd("~")

		log("Sending script...")
		self.remote.send_file(FILE_TO_SEND, REMOTE_FILE)

		self.active = True
		# Run sent file and wait until it ends
		log("Running script...")
		streams = self.remote.exec_command_sync(Cfg.get().remote_python_command + " " + REMOTE_FILE)
		log("Output:")
		for line in streams.get_stdout_lines():
			print("\t" + line)
		self.active = False

		self.remote.close()
		return True

	def end(self):
		if self.active:
			raise IllegalOperationError("A synchronous attack cannot be stopped while it's running.")
