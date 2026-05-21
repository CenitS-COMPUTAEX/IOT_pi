from attacks.attack_type import AttackType
from defs.attack_event.attack_event import AttackEvent, AttackAction
from defs.attack_event.event_time import EventTime


class AttackEventFactory:
	"""
	Used to create attack events
	"""

	# Timestamp of the start of the event list
	list_start_time: float

	def __init__(self, list_start_time: float):
		"""
		Instantiates a new factory that will be used to create events as part of an event list.

		list_start_time: Timestamp of the start of the event list, in seconds.
		"""
		self.list_start_time = list_start_time

	def start_event(self, time: float, device_num: int, attack: AttackType) -> AttackEvent:
		"""
		Creates a new attack start event
		time: Timestamp marking when the attack should start
		device_num: Number of the device that will be attacked
		"""
		event_time = EventTime(self.list_start_time, time)
		return AttackEvent(event_time, AttackAction.START, device_num, attack)

	def end_event(self, time: float, device_num: int, attack: AttackType) -> AttackEvent:
		"""
		Creates a new attack end event
		time: Timestamp marking when the attack should end
		device_num: Number of the device under attack
		"""
		event_time = EventTime(self.list_start_time, time)
		return AttackEvent(event_time, AttackAction.END, device_num, attack)

	def end_all_event(self, time: float) -> AttackEvent:
		"""
		Creates a new end all attacks event
		time: Timestamp marking when the event should happen
		"""
		event_time = EventTime(self.list_start_time, time)
		return AttackEvent(event_time, AttackAction.END_ALL, None, None)
