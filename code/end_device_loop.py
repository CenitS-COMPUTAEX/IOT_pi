import math
import os
import random
import sys
import time

from data.buffer_data_writer import BufferDataWriter
from defs.utils import log
from defs.config import Config as Cfg

"""
Script run by an end device. It generates fake power usage data and writes it to a cyclic buffer CSV file.

The CSV file has 2 columns:
	Time: UNIX timestamp in ms
	Power: Power usage of the device
"""


def main():
	args = sys.argv

	if len(args) != 3:
		print_help()
	else:
		run(args[1], int(args[2]))


def print_help():
	print("Usage: " + get_script_name(sys.argv[0]) + " output_path buffer_size\n"
		"buffer_size: Amount of measurements that will be stored in the buffer")


def run(output_path: str, buffer_size: int):
	"""
	Runs the program until the user interrupts it with Ctrl+C.
	output_path: Path to the file that should be used as the output buffer. If it already exists, it will be
	truncated.
	buffer_size: Amount of entries to write on the output buffer. Once that limit is reached, older entries
	will start getting overwritten.
	"""
	os.makedirs(os.path.dirname(output_path), exist_ok=True)
	writer = BufferDataWriter(output_path, False, buffer_size)

	# Variables used to write fake power data
	attack_status = False  # False to write low power values, true to write high power values
	time_until_status_change = random.randrange(10, 21)
	last_print = math.ceil(time_until_status_change)

	while True:
		time_start = time.time()

		if time_until_status_change <= 0:
			time_until_status_change = random.randrange(10, 21)
			last_print = math.ceil(time_until_status_change)
			attack_status = not attack_status

		if math.floor(time_until_status_change) < last_print:
			print("Attack status: " + str(attack_status) + ", time until change: " +
				str(math.floor(time_until_status_change)))
			last_print = math.floor(time_until_status_change)

		writer.write(random.randrange(400, 651) if attack_status else 300)

		time_end = time.time()
		# Time to wait until the next measurement
		time_wait = time_start + Cfg.get().measurement_delay - time_end
		if time_wait >= 0:
			time.sleep(time_wait)
		else:
			log("Warning: Can't keep up with the set measurement delay! " + str(time_wait * -1000) +
				" ms of additional delay were introduced.")

		time_until_status_change -= time.time() - time_start


def get_script_name(argv0: str):
	"""
	Returns the name of the executed file given the full path to it (argv[0])
	"""
	return argv0.replace("\\", "/").split("/")[-1]


if __name__ == "__main__":
	main()
