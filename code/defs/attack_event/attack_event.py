from datetime import datetime
from enum import Enum

from attacks.attack_type import AttackType
from defs.attack_event.event_time import EventTime


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

	# Stores relevant timestamps for this event, such as the start timestamp
	time: EventTime
	# Action to perform (start or end an attack)
	action: AttackAction
	# Device to run the attack on
	device_num = int
	# Attack to run
	attack: AttackType

	def __init__(self, time: EventTime, action: AttackAction, device_num: "int | None", attack: "AttackType | None"):
		self.time = time
		self.action = action
		self.device_num = device_num
		self.attack = attack

	def get_time(self) -> float:
		"""
		Returns the timestamp that marks when the event should start, in seconds.
		"""
		return self.time.event_time

	def __str__(self) -> str:
		result = ""
		result += self.action.name
		if self.action != AttackAction.END_ALL:
			result += " " + self.attack.name + " - device: " + str(self.device_num) + ", "
		else:
			result += " - "
		result += "time: " + datetime.fromtimestamp(self.get_time()).strftime('%Y-%m-%d %H:%M:%S')
		result += " (offset: " + self.time.get_offset_str() + ")"
		return result
