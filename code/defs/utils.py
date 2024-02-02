import time
from datetime import datetime
from typing import List

from attacks.attack_type import AttackType
from defs.constants import Constants as Cst


def log(msg: str):
	"""
	Logs a message to the console, including the current time and date.
	"""

	time_str = datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
	print("[" + time_str + "] " + msg)


def print_with_indent(lines: List[str], indent_level: int):
	"""
	Prints a list of messages, adding a certain amount of tab characters before each line.
	"""
	for line in lines:
		print("\t" * indent_level + line)


def compatible_attacks(attack1: AttackType, attack2: AttackType) -> bool:
	"""
	Returns whether two attacks are compatible or not
	return: True if both attacks are compatible, false if they can't be running at the same time on the same device.
	"""
	for pair in Cst.INCOMPATIBLE_ATTACKS:
		if pair[0] == attack1 and pair[1] == attack2 or pair[1] == attack1 and pair[0] == attack2:
			return False
	return True
