import time

from data.data_writer import DataWriter
from defs.utils import log


class BufferDataWriter(DataWriter):
	"""
	Class that can be used to write power and attacks data to a file while treating it as a cyclic buffer.
	Older data will be overwritten with newer data on each write.
	"""

	file_path: str
	attack_column: bool
	buffer_size: int

	def __init__(self, file_path: str, attack_column: bool, buffer_size: int):
		"""
		Instantiates the class to write to the specified file.
		buffer_size: Size of the buffer file. Once it fills, older entries will start getting replaced.
		"""
		self.file_path = file_path
		self.attack_column = attack_column
		self.buffer_size = buffer_size

		file = open(self.file_path, "w")
		# The first line contains the number of the most recently written entry, with the first entry being #0.
		# We write -1 to indicate that no entries are present in the buffer yet.
		file.write("-1" + "\n")
		self._write_header(file)
		file.close()

	def write(self, power: float, attacks: int = -1, timestamp: float = -1):
		"""
		Updates the output buffer, writing the current power usage into a new entry. If the buffer is full, the oldest
		entry will be overwritten.
		The first line in the buffer file, which indicates which buffer entry was most recently overwritten, will be
		updated accordingly. The second line in the file, the CSV header, will remain untouched.
		See DataWriter.write for the description of the base method.
		"""
		file = open(self.file_path, "r+")
		# Since the buffer is small, we just read the whole file and manipulate it in memory, since it's easier
		lines = file.read().split("\n")
		if lines[-1] == "":
			lines.pop(-1)
		# Read the most recent entry value first
		most_recent_entry = int(lines[0])

		if timestamp == -1:
			timestamp = int(time.time() * 1000)

		string_to_write = self._get_csv_line(power, timestamp, attacks)
		# Check if we need to append or overwrite the new entry
		entry_to_replace = (most_recent_entry + 1) % self.buffer_size
		last_entry = len(lines) - 3
		if entry_to_replace <= last_entry:
			# Replace the entry
			lines[entry_to_replace + 2] = string_to_write
			lines[0] = str(entry_to_replace)
		elif entry_to_replace == last_entry + 1:
			# Add new line
			lines.append(string_to_write)
			lines[0] = str(entry_to_replace)
		else:
			log("Error: Output buffer in inconsistent state: Most recent entry is #" + str(most_recent_entry) + ", but "
				"the last entry in the file is #" + str(last_entry) + ". Buffer will be truncated.")
			# Keep only the header lines and write a new entry as the first entry
			lines = lines[0:2]
			lines.append(string_to_write)
			lines[0] = "0"

		file.seek(0)
		file.truncate()
		file.write("\n".join(lines))
		file.close()

	def _has_attack_column(self):
		return self.attack_column
