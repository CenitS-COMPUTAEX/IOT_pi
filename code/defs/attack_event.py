from datetime import datetime
from enum import Enum

from attacks.attack_type import AttackType


class AttackAction(Enum):
	"""
	Possible actions that can be performed during an event
	"""
	START = 0  # Start an attack
	END = 1  # End an attack
	END_ALL = 2  # End all attacks


class AttackEvent:
	"""
	Represents an event that takes place during an attack generation test
	"""

	# Timestamp that indicates when the action should be performed
	time: float
	# Action to perform (start or end an attack)
	action: AttackAction
	# Device to run the attack on
	device_num = int
	# Attack to run
	attack: AttackType

	def __init__(self, time: float, action: AttackAction, device_num: "int | None", attack: "AttackType | None"):
		self.time = time
		self.action = action
		self.device_num = device_num
		self.attack = attack

	@classmethod
	def start_event(cls, time: float, device_num: int, attack: AttackType):
		return cls(time, AttackAction.START, device_num, attack)

	@classmethod
	def end_event(cls, time: float, device_num: int, attack: AttackType):
		return cls(time, AttackAction.END, device_num, attack)

	@classmethod
	def end_all_event(cls, time: float):
		return cls(time, AttackAction.END_ALL, None, None)

	def __str__(self) -> str:
		result = ""
		result += self.action.name
		if self.action != AttackAction.END_ALL:
			result += " " + self.attack.name + " - device: " + str(self.device_num) + ", "
		else:
			result += " - "
		result += "time: " + datetime.fromtimestamp(self.time).strftime('%Y-%m-%d %H:%M:%S')
		return result
