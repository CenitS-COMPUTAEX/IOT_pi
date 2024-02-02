from abc import ABC, abstractmethod
from typing import TextIO


class DataWriter(ABC):
	"""
	Base class that can be used to write power and optionally also attacks data to a file.
	"""

	COLUMN_TIME = "Time"
	COLUMN_ATTACKS = "Attacks"
	COLUMN_POWER = "Power"

	@abstractmethod
	def write(self, power: float, attacks: int = -1, timestamp: float = -1):
		"""
		Writes a new entry to the file.
		power: Power usage of the device
		attacks: Active attacks on the device. If not specified, no attack data will be written.
		timestamp: Timestamp to write to the file. If not specified, the current system time in ms will be written.
		"""
		...

	@abstractmethod
	def _has_attack_column(self):
		"""
		Returns true if the output file includes an attack column
		"""
		...

	def _write_header(self, file: TextIO):
		"""
		Writes the header of the output file
		file: Output file
		"""
		if self._has_attack_column():
			file.write(",".join([self.COLUMN_TIME, self.COLUMN_ATTACKS, self.COLUMN_POWER]) + "\n")
		else:
			file.write(",".join([self.COLUMN_TIME, self.COLUMN_POWER]) + "\n")

	def _get_csv_line(self, power: float, timestamp: float, attacks: int = -1) -> str:
		"""
		Gets the text string that needs to be written to the output file
		"""
		if self._has_attack_column():
			return str(timestamp) + "," + ("" if attacks == -1 else str(attacks)) + "," + str(power)
		else:
			return str(timestamp) + "," + str(power)
