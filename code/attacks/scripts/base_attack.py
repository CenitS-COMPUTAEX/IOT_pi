import time
from abc import ABC, abstractmethod

from defs import utils
from defs.std_streams import StdStreams
from defs.utils import log


class BaseAttack(ABC):
	"""
	Abstract class that represents an attack that can be run on a machine
	"""

	@abstractmethod
	def get_attack_name(self) -> str:
		"""
		Returns the name of the attack. Meant to be used when printing messages.
		"""
		...

	@abstractmethod
	def is_synchronous(self) -> bool:
		"""
		Returns whether the attack is synchronous or not
		"""
		...

	@abstractmethod
	def start(self, device_num: int) -> bool:
		"""
		Starts the attack on the specified device.
		If the attack is synchronous, the method doesn't return until it ends.
		Return: True if the attack was started successfully, false if it wasn't
		"""
		...

	@abstractmethod
	def end(self):
		"""
		Ends the attack. If the attack is synchronous and it's currently active, throws IllegalOperationError
		(since synchronous attacks can't be stopped once they are running).
		"""
		...

	def _check_exit(self, streams: StdStreams):
		"""
		Waits until the remote program exits and checks the exit code. If it's not 0, an error message will be
		printed, alongside any errors printed by the remote device during program execution.
		Meant to run on a separate thread since it's a blocking call.
		streams: StdStreams object created when launching the remote program
		"""

		# Wait until the remote program is done. We can't call recv_exit_status() directly since that blocks
		# the execution, even across threads.
		while not streams.stdout.channel.exit_status_ready():
			time.sleep(0.5)
		exit_code = streams.stdout.channel.recv_exit_status()

		# Check if the program exited normally (or if it was killed when the remote connection was closed, which
		# results in an exit code of -1)
		if exit_code != 0 and exit_code != -1:
			self._print_remote_error(exit_code, streams)

	def _print_remote_error(self, exit_code: int, streams: StdStreams):
		"""
		Prints an error message caused by an error when running a script remotely
		attack_name: Name of the attack that caused the error
		exit_code: Exit code of the remote program
		streams: Object containing the streams associated with the remote script execution
		"""
		log(self.get_attack_name() + " attack: Error: Remote script exited with status " + str(exit_code) +
			". The attack won't actually be run.\n"
			"Remote script's stderr trace:")
		utils.print_with_indent(streams.get_stderr_lines(), 1)
		stdout_lines = streams.get_stdout_lines()
		if len(stdout_lines) > 0:
			print("Remote script's stdout trace" + (" (last 200 lines)" if len(stdout_lines) > 200 else "") + ":")
			utils.print_with_indent(stdout_lines[-200:], 1)
