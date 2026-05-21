import os
from enum import Enum
from defs.constants import Constants as Cst

"""
Utility file used to flag the start and end of an attack by creating and updating the required files
"""

ATTACK_LOG_PATH = "data/attack_log.csv"
ATTACK_LOG_HEADER = "Time start,Time end,Device,Attack"


class Status(Enum):
	"""
	Used as the return value of most methods
	"""
	SUCCESS = 0
	ERROR_ATTACK_FILE_ALREADY_EXISTS = 1
	ERROR_ATTACK_FILE_DOES_NOT_EXIST = 2
	OS_ERROR = 3


def flag_attack_start(device_num: int, attack_num: int) -> Status:
	"""
	Flags the start of an attack, creating the attack file.
	"""

	file_path = get_attack_file(device_num, attack_num)
	if os.path.isfile(file_path):
		return Status.ERROR_ATTACK_FILE_ALREADY_EXISTS
	else:
		os.makedirs(os.path.dirname(file_path), exist_ok=True)
		try:
			open(file_path, "a")  # Create empty file
			return Status.SUCCESS
		except OSError:
			return Status.OS_ERROR


def flag_attack_end(device_num: int, attack_num: int, time_start: int, time_end: int) -> Status:
	"""
	Flags the end of an attack, deleting the attack file and writing the attack to the attack log.
	time_start and time_end specify the start and end time of the attack as UNIX time in ms
	"""

	file_path = get_attack_file(device_num, attack_num)
	if os.path.isfile(file_path):
		try:
			os.remove(file_path)

			# Log attack
			file_exists = os.path.isfile(ATTACK_LOG_PATH)
			with open(ATTACK_LOG_PATH, "a") as attack_log:
				if not file_exists:
					attack_log.write(ATTACK_LOG_HEADER + "\n")
				attack_log.write(str(time_start) + "," + str(time_end) + "," + str(device_num) + "," + str(attack_num) + "\n")
			return Status.SUCCESS
		except OSError:
			return Status.OS_ERROR
	else:
		return Status.ERROR_ATTACK_FILE_DOES_NOT_EXIST


def can_start_attack(device_num: int, attack_num: int) -> Status:
	"""
	Returns a status value specifying if it's possible to start the specified attack on the specified device.
	If the attack file already exists, returns Status.ERROR_ATTACK_FILE_ALREADY_EXISTS.
	Otherwise, returns Status.SUCCESS.
	"""
	file_path = get_attack_file(device_num, attack_num)
	if os.path.isfile(file_path):
		return Status.ERROR_ATTACK_FILE_ALREADY_EXISTS
	else:
		return Status.SUCCESS


def can_end_attack(device_num: int, attack_num: int) -> Status:
	"""
	Returns status value specifying if it's possible to end the specified attack on the specified device.
	If the attack file does not exist, returns Status.ERROR_ATTACK_FILE_DOES_NOT_EXIST.
	Otherwise, returns Status.SUCCESS.
	"""
	file_path = get_attack_file(device_num, attack_num)
	if os.path.isfile(file_path):
		return Status.SUCCESS
	else:
		return Status.ERROR_ATTACK_FILE_DOES_NOT_EXIST


def delete_all_attack_files() -> Status:
	"""
	Forcefully deletes all the existing attack files without logging anything.
	"""
	if os.path.exists(Cst.ATTACK_FOLDER):
		for file in os.listdir(Cst.ATTACK_FOLDER):
			path = os.path.join(Cst.ATTACK_FOLDER, file)
			try:
				if os.path.isfile(path):
					os.remove(path)
			except OSError:
				return Status.OS_ERROR
	return Status.SUCCESS


def get_attack_file(device_num: int, attack_num: int):
	"""
	Returns the path to the file that indicates that the specified attack is active on the specified device
	"""
	return os.path.join(Cst.ATTACK_FOLDER, Cst.ATTACK_FILE_PREFIX + str(device_num) + "-" + str(attack_num))
