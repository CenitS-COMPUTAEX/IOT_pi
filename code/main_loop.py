import os
import sys
import time
from threading import Thread, Event
from typing import List

from data.buffer_data_writer import BufferDataWriter
from data.data_writer import DataWriter
from data.standard_data_writer import StandardDataWriter
from defs.utils import log
# noinspection PyPackageRequirements
# Reason: The IDE incorrectly assumes this is a library that needs to be added to requirements.txt
from lib import SDL_Pi_INA3221
from attacks.attack_type import AttackType
from attacks.attack_generator import NormalParams, AttackGenerator
from defs.constants import Constants as Cst
from defs.config import Config as Cfg

"""
Script run by the main device. It reads the status of the end devices and writes it to a CSV file.
Power usage data is read using the SDL_Pi_INA3221 library.
Attack data is read from files under the attacks/ directory. This directory is expected to contain one file for
each active attack on each device, named "attack-X-Y", where X is the number that represents the attacked device
and Y is the number that represents the attack in progress.
Attack scripts should ensure the corresponding file is created and deleted when an attack starts and ends.
(Existing attack scripts already handle this automatically)

The CSV file has 3 columns:
	Time: UNIX timestamp in ms
	Attacks: Indicates which attack(s) were active on the device. Each bit represents an attack.
		Example: A value of 3 (bits 0 and 1 set) means both attack #0 and #1 are active.
	Power: Power usage of the device

This script also allows performing automated attacks given some user-specified parameters.
"""

ina3221 = SDL_Pi_INA3221.SDL_Pi_INA3221(addr=0x40)

NUM_DEVICES = 3


def main():
	args = sys.argv

	# Parse flags
	if "--help" in args:
		print_help()
	else:
		print_events = False
		exit_early = False
		buffer_size = 0
		event_seed = None

		if "-a" in args:
			args.remove("-a")

			# Required parameters
			value = pop_flag_param(args, "--devices")
			if value is None:
				print_help()
				return 1
			devices = [int(d) for d in value.split(",")]

			value = pop_flag_param(args, "--duration")
			if value is None:
				print_help()
				return 1
			duration = int(value)

			value = pop_flag_param(args, "--delay")
			if value is None:
				print_help()
				return 1
			delay = NormalParams.from_str(value)

			# Optional parameters
			generator = AttackGenerator(devices, duration, delay)

			value = pop_flag_param(args, "--attacks")
			if value is not None:
				attacks = [AttackType.from_str(v) for v in value.split(",")]
				if len(attacks) == 0:
					print("Error: At least one attack must be specified")
					return 1
				generator.allowed_attacks = attacks
			value = pop_flag_param(args, "--multi-chance")
			if value is not None:
				float_val = float(value)
				if float_val < 0 or float_val > 100:
					print("Error: Multi-attack chance must be between 0 and 100")
					return 1
				generator.multiple_attack_chance = float_val / 100
			value = pop_flag_param(args, "--attack-duration")
			if value is not None:
				params = NormalParams.from_str(value)
				if params.mean <= 0 or params.std <= 0:
					print("Error: Attack duration params must be positive")
					return 1
				generator.attack_duration = params
			value = pop_flag_param(args, "--min-attack-duration")
			if value is not None:
				float_val = float(value)
				if float_val <= 0:
					print("Error: Minimum attack duration must be positive")
					return 1
				generator.min_attack_duration = float_val
			value = pop_flag_param(args, "--min-delay")
			if value is not None:
				float_val = float(value)
				if float_val <= 0:
					print("Error: Minimum attack delay must be positive")
					return 1
				generator.min_delay = float_val
			value = pop_flag_param(args, "--short-chance")
			if value is not None:
				float_val = float(value)
				if float_val < 0 or float_val > 100:
					print("Error: Short attack chance must be between 0 and 100")
					return 1
				generator.short_attack_chance = float_val / 100
			value = pop_flag_param(args, "--short-duration")
			if value is not None:
				float_val = float(value)
				if float_val <= 0:
					print("Error: Short attack duration must be positive")
					return 1
				generator.short_attack_scale = float_val

			# Optional flags
			if "-l" in args:
				args.remove("-l")
				print_events = True
			if "-d" in args:
				args.remove("-d")
				exit_early = True
			value = pop_flag_param(args, "-s")
			if value is not None:
				event_seed = int(value)
		else:
			generator = None

		if "-b" in args:
			buffer_size = int(pop_flag_param(args, "-b"))
			if buffer_size <= 0:
				print("Error: Buffer size must be > 0")
				return 1

		log_attacks = True
		if "-na" in args:
			args.remove("-na")
			log_attacks = False

		run(generator, print_events, exit_early, buffer_size, log_attacks, event_seed)


def run(generator: "AttackGenerator | None", print_events: bool, exit_early: bool, buffer_size: int, log_attacks: bool,
	event_seed: int = None):
	"""
	Runs the program. If an attack generator has been provided, it will be launched on a separate thread.
	The program will also end its execution after the specified duration for the generator is complete.
	print_events: If true and a generator is present, the list of attack events that will be run by the generator
	will be printed.
	exit_early: If true, the program will exit early. No files will be created and no attacks will be started.
	The attack list will still be printed if required.
	buffer_size: If > 0, data will be written to a cyclic buffer instead of to a regular file.
	log_attacks: True to add a column to the data listing the currently active attacks
	event_seed: If specified, this seed will be used to initialize the RNG used to generate the attack list.
	"""
	if generator is None:
		end_time = -1
		generator_thread = None
		if exit_early:
			return
	else:
		end_time = time.time() + generator.duration * 60
		generator.stop_flag = Event()
		events = generator.create_event_list(event_seed)
		if print_events:
			print("Event generation seed: " + str(generator.seed))
			log("List of attack events that will be run:")
			print("\n".join([str(e) for e in events]))
		if exit_early:
			return
		generator_thread = Thread(target=generator.start)
		generator_thread.start()

	os.makedirs(Cst.ATTACK_FOLDER, exist_ok=True)
	for i in range(NUM_DEVICES):
		os.makedirs(os.path.dirname(get_file_path(i + 1, buffer_size > 0)), exist_ok=True)
	writers = []
	if buffer_size > 0:
		for i in range(NUM_DEVICES):
			writers.append(BufferDataWriter(get_file_path(i + 1, True), log_attacks, buffer_size))
	else:
		for i in range(NUM_DEVICES):
			writers.append(StandardDataWriter(get_file_path(i + 1, False), log_attacks))

	log("Main loop started")
	try:
		while end_time == -1 or time.time() < end_time:
			time_start = time.time()

			for i, writer in enumerate(writers):
				write_csv_line(writer, i + 1)

			time_end = time.time()
			# Time to wait until the next measurement
			time_wait = time_start + Cfg.get().measurement_delay - time_end
			if time_wait >= 0:
				time.sleep(time_wait)
			else:
				log("Warning: Can't keep up with the set measurement delay! " + str(time_wait * -1000) +
					" ms of additional delay were introduced.")
	except KeyboardInterrupt:
		if generator is not None:
			# Signal the generator so it ends its execution
			generator.stop_flag.set()

	if buffer_size > 0:
		write_buffer_end()

	if generator is not None:
		log("Waiting for attack generator to exit...")
		generator_thread.join()

	log("Main loop stopped")


def write_csv_line(writer: DataWriter, device_num: int):
	"""
	Writes a single line to the CSV file associated with the specified device
	device_num: Number identifying the device whose data should be written
	"""

	power = ina3221.getCurrent_mA(device_num)

	# Check active attacks on this device
	attacks = 0
	for attack_file in os.listdir(Cst.ATTACK_FOLDER):
		if os.path.isfile(os.path.join(Cst.ATTACK_FOLDER, attack_file)):
			file_split = attack_file.split("-")
			device_id = int(file_split[1])
			if device_id == device_num:
				attack_id = int(file_split[2])
				attacks |= 1 << attack_id

	writer.write(power, attacks)


def get_file_path(device_num: int, buffer_mode: bool) -> str:
	"""
	Returns the path to the file where the data for a given device should be written
	device_num: Number identifying the device where data will be read from
	buffer_mode: True if the file will be written in buffer mode
	"""
	string = "data/" + "data-channel-" + str(device_num) + "/"
	if buffer_mode:
		string += "buffer.csv"
	else:
		string += time.strftime("%Y-%m-%d %H-%M-%S") + ".csv"
	return string


def write_buffer_end():
	"""
	Writes the end keyword in all the data buffers to signal that the execution has ended.
	"""
	with open(get_file_path(1, True), "w") as f:
		f.write(Cst.BUFFER_OVER_KEYWORD)
	with open(get_file_path(2, True), "w") as f:
		f.write(Cst.BUFFER_OVER_KEYWORD)
	with open(get_file_path(3, True), "w") as f:
		f.write(Cst.BUFFER_OVER_KEYWORD)


def print_help():
	print("Flags: \n"
		"--help: Prints this help\n"
		"-a: Launches with the attack generator active. The tool will randomly start attacks according to the following "
		"flags:\n"
			"\t--devices: (Required) List of comma-separated device numbers where attacks will be sent to.\n"
			"\t--duration <time>: (Required) Duration (in minutes) of the test. Once time is up, all attacks will "
			"be stopped and the program will exit.\n"
			"\t--delay: (Required) Two comma-separated values indicating the mean and standard deviation of the "
			"normal distribution used to generate delays between attacks. Unit: minutes.\n"
			"\t--attacks: List of comma-separated values indicating the attacks that can be started. Possible values:\n"
				"\t  mining (0): Cryptocurrency mining attack\n"
				"\t  login (1): Brute force login attack\n"
				"\t  crypt (2): File encryption attack\n"
				"\t  pass (3): Password guessing attack\n"
				"\t  lite-mining (4): Cryptocurrency mining attack (only 2 threads)\n"
			"\tDefaults to all existing attacks.\n"
			"\t--multi-chance: Chance of launching addidtional attacks. The chance of launching n attacks with a "
			"parameter value of p will be p^(n - 1). Range: [0,100], default: 20.\n"
			"\t--attack-duration: Two comma-separated values indicating the mean and standard deviation of the "
			"normal distribution used to generate the duration of attacks. Unit: minutes, default: 3,1.\n"
			"\t--min-attack-duration: Minimum attack duration, in seconds. Default: 5.\n"
			"\t--min-delay: Minimum delay between attacks, in seconds. Default: 30.\n"
			"\t--short-chance: Chance of performing a short attack. Short attacks use an exponential distribution "
			"to generate their duration. Range: [0,100], default: 20.\n"
			"\t--short-duration: Beta parameter of the exponential distribution used to generate the duration "
			"of short attacks. This parameter corresponds to the average duration. Unit: seconds, default: 15.\n"
			"\n"
			"\t-l: Print all the attacks that will be run by the attack generator.\n"
			"\t-s <seed>: Set the RNG seed used to generate the attack list. Must be an integer.\n"
		"-d: Don't actually run any attacks, just exit early. The attack list will still be printed if required.\n"
		"-b <size>: Run in buffer mode. The most recent <size> reads will be written to a buffer, with older "
		"entries being overwritten by newer ones.\n"
		"-na: Do not log active attacks alongside power reads. Useful when deploying the tool in a scenario "
		"where controlled attacks will not take place.\n"
		"Use Ctrl+C to quit, stopping all active attacks if there's any running.\n")


def pop_flag_param(args: List[str], flag: str) -> "str | None":
	"""
	Given the list of arguments passed to the programs and a flag, returns the value of said flag and removes both
	the flag and the value from the argument list.
	If the flag isn't present or it doesn't have a value, returns None.
	"""
	try:
		pos = args.index(flag)
		if pos == len(args) - 1:
			return None
		val = args[pos + 1]
		del args[pos:pos + 2]
		return val
	except ValueError:
		return None


if __name__ == "__main__":
	main()
