import time
from typing import TextIO

from data.data_writer import DataWriter
from defs.exceptions import IllegalOperationError


class StandardDataWriter(DataWriter):
	"""
	Class that can be used to write power and attacks data to a regular file, appending new lines at the end.
	"""

	# File used when buffer_mode is false
	file: TextIO
	attack_column: bool

	def __init__(self, file_path: str, attack_column: bool):
		"""
		Instantiates the class to write to the specified file. If the file already exists, it will be truncated.
		The file will remain open until close() is called.
		attack_column: True to include a column in the output file listing active attacks.
		"""
		self.file = open(file_path, "w")
		self.attack_column = attack_column
		self._write_header(self.file)

	def write(self, power: float, attacks: int = -1, timestamp: float = -1):
		"""
		Writes one line to the output file. If close() has already been called, throws IllegalOperationError.
		See DataWriter.write for the description of the base method.
		"""
		if self.file.closed:
			raise IllegalOperationError("Cannot write to a file that has already been closed.")

		if timestamp == -1:
			timestamp = int(time.time() * 1000)

		self.file.write(self._get_csv_line(power, timestamp, attacks) + "\n")

	def close(self):
		"""
		Closes the file that was opened when instantiating the class. Attempting to call write() file after calling
		this method will throw an exception.
		"""
		self.file.close()

	def _has_attack_column(self):
		return self.attack_column
