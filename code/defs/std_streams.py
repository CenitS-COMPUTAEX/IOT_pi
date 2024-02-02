from typing import Tuple, List

from paramiko.channel import ChannelStdinFile, ChannelFile, ChannelStderrFile


class StdStreams:
	"""
	Class containing streams created by a SSHClient.exec_command() call
	"""

	stdin: ChannelStdinFile
	stdout: ChannelFile
	stderr: ChannelStderrFile

	def __init__(self, streams: Tuple[ChannelStdinFile, ChannelFile, ChannelStderrFile]):
		self.stdin = streams[0]
		self.stdout = streams[1]
		self.stderr = streams[2]

	def get_stdout_lines(self) -> List[str]:
		"""
		Returns all the lines contained in the stdout stream as a list
		"""
		output = []
		for line in self.stdout.read().decode("utf-8").splitlines():
			output.append(line)
		return output

	def get_stderr_lines(self) -> List[str]:
		"""
		Returns all the lines contained in the stderr stream as a list
		"""
		output = []
		for line in self.stderr.read().decode("utf-8").splitlines():
			output.append(line)
		return output
