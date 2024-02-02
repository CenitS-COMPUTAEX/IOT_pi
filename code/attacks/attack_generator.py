import random
import sys
import time
from functools import cmp_to_key

from typing import List

from attacks.attack_type import AttackType
from attacks.attack_tool import AttackTool
from defs.attack_event import AttackEvent, AttackAction
from defs.exceptions import IllegalOperationError
from defs.utils import compatible_attacks


class NormalParams:
	"""
	Parameters of a normal distribution
	"""
	mean: float
	std: float

	def __init__(self, avg: float, std: float):
		self.mean = avg
		self.std = std

	@classmethod
	def from_str(cls, string: str):
		"""
		Creates a new instance of this class given a string that contains both the mean and the std separated
		by a comma
		"""
		split = string.split(",")
		return cls(float(split[0]), float(split[1]))


class AttackGenerator:
	"""
	Class used to randomly start and stop attacks
	"""

	# List of device ids that the attacks will be sent to
	devices: List[int]

	# Lists all the attacks that can be started by the script
	allowed_attacks: List[AttackType]
	# Chance of starting an additional attack whenever an attack is started. Range: [0,1]
	# This chance is reapplied whenever an additional attack is started, so the chance of starting n attacks with
	# a parameter value of p is p^(n - 1).
	multiple_attack_chance: float
	# Duration of the attack generation period, in minutes
	duration: int

	# Parameters used to determine the time between attacks, in minutes
	attack_delay: NormalParams
	# Parameters used to determine the duration of an attack, in minutes
	attack_duration: NormalParams
	# Minimum attack duration, in seconds.
	min_attack_duration: float
	# Minimum delay between attacks, in seconds.
	min_delay: float
	# Chance of starting a short attack. Range: [0,1]
	short_attack_chance: float
	# Beta parameter (1/lambda) used to determine the duration of short attacks, which follows an exponential
	# distribution. This value is also the mean of the distribution, that is, the mean duration of the attack.
	# Unit: Seconds
	short_attack_scale: float

	attack_tool: AttackTool
	# List of events that will take place during the test
	events: List[AttackEvent]
	# Used to stop the program early when it's run as a thread created externally
	stop_flag: "Event | None"
	# Seed used to generate the event list. None if no event list has been generated yet.
	seed: "int | None"

	def __init__(self, devices: List[int], duration: int, attack_delay: NormalParams):
		"""
		Creates a new instance with the minimum required parameters. The rest are set to their defaults.
		"""
		if len(devices) == 0:
			raise ValueError("At least one device must be specified")
		if duration <= 0:
			raise ValueError("Duration must be positive")
		if attack_delay.mean <= 0 or attack_delay.std <= 0:
			raise ValueError("Attack delay parameters must be positive")

		self.devices = devices

		self.allowed_attacks = [AttackType.MINING, AttackType.LOGIN, AttackType.ENCRYPTION]
		self.multiple_attack_chance = 0.2
		self.duration = duration
		self.attack_delay = attack_delay
		self.attack_duration = NormalParams(3, 1)
		self.min_attack_duration = 10
		self.min_delay = 30
		self.short_attack_chance = 0.2
		self.short_attack_scale = 15  # Mean: 15 seconds

		self.attack_tool = AttackTool(True)
		self.events = []
		self.seed = None

		self.stop_flag = None

	def start(self):
		"""
		Starts generating attacks until the event list is empty, a keyboard interrupt is received, or the stop flag
		is set.
		create_event_list() must be called before this method is so the event list is created. If create_event_list()
		has not been called yet, throws IllegalOperationError.
		"""
		if len(self.events) == 0:
			raise IllegalOperationError("Cannot start attack generator without an event list. "
				"Call create_event_list() first.")

		self.attack_tool.clean_attack_files()
		try:
			while len(self.events) > 0 and not self._should_stop():
				event = self.events[0]
				# Wait until the event starts if required
				# We also need to periodically check the stop flag
				while True:
					if self._should_stop():
						break
					wait_time = event.time - time.time()
					if wait_time <= 0:
						break
					# Check the stop flag every 5 seconds
					time.sleep(min(5.0, wait_time))

				if not self._should_stop():
					if event.action == AttackAction.START:
						self.attack_tool.start_attack(event.device_num, event.attack)
					elif event.action == AttackAction.END:
						self.attack_tool.end_attack(event.device_num, event.attack)
					elif event.action == AttackAction.END_ALL:
						self.attack_tool.end_all_attacks()
					self.events.pop(0)
		except KeyboardInterrupt:
			self.attack_tool.end_all_attacks()

		if self._should_stop():
			self.attack_tool.end_all_attacks()

	def create_event_list(self, seed: int = None) -> List[AttackEvent]:
		"""
		Creates the list of events that will be used during attack generation. Events will be generated for each
		device separately, but they will all be inserted into a single event list.
		seed: If specified, this value will be used as the RNG seed. If None, a random seed will be used.

		Warning: This list contains the timestamps when the different attacks will start and end. Ideally, this
		method should be called right before start(). Otherwise, some of the first events might be run all at
		once since their start time has already passed.
		"""
		if seed is None:
			self.seed = random.randrange(sys.maxsize)
		else:
			self.seed = seed
		random.seed(self.seed)

		start_time = time.time()
		end_time = start_time + self.duration * 60
		for device_num in self.devices:
			# Marks the current time in the generation process
			current_time = start_time
			while current_time < end_time:
				# Random delay until next attack
				delay = random.normalvariate(self.attack_delay.mean, self.attack_delay.std) * 60
				if delay < self.min_delay:
					delay = self.min_delay
				current_time += delay
				if current_time >= end_time:
					break

				# Determine the number of attacks
				num_attacks = 1
				while random.random() < self.multiple_attack_chance and num_attacks < len(self.allowed_attacks):
					num_attacks += 1

				# Generate all the attacks. Each one will have a different type.
				possible_attacks = self.allowed_attacks.copy()
				active_attacks = []
				for i in range(num_attacks):
					if len(possible_attacks) > 0:
						# Generate single attack
						attack = possible_attacks.pop(random.randrange(len(possible_attacks)))
						self._remove_incompatible(attack, possible_attacks)
						attack_event = AttackEvent.start_event(current_time, device_num, attack)
						# Store in event list
						self.events.append(attack_event)
						active_attacks.append(attack_event)

				num_attacks = len(active_attacks)

				# Stop each attack after a random amount of time
				durations = self._get_attacks_duration(num_attacks)
				for duration in durations:
					if current_time + duration >= end_time:
						break

					# End one of the remaining active attacks
					attack_to_end = active_attacks.pop(random.randrange(len(active_attacks)))
					self.events.append(
						AttackEvent.end_event(current_time + duration, attack_to_end.device_num, attack_to_end.attack))

				current_time += durations[-1]
				assert(current_time >= self.events[-1].time)
		# End all remaining attacks
		self.events.append(AttackEvent.end_all_event(end_time))

		# Sort the list by event time
		self.events.sort(key=cmp_to_key(lambda ev1, ev2: ev1.time - ev2.time))
		return self.events

	def _get_attacks_duration(self, num_attacks: int) -> List[float]:
		"""
		Given a number of attacks, generates a duration for each one of them, in seconds.
		The resulting list will be in ascending order.
		"""
		durations = []
		for i in range(num_attacks):
			if random.random() < self.short_attack_chance:
				duration = random.expovariate(1 / self.short_attack_scale)
			else:
				duration = random.normalvariate(self.attack_duration.mean, self.attack_duration.std) * 60
			if duration < self.min_attack_duration:
				duration = self.min_attack_duration
			durations.append(duration)
		durations.sort()
		return durations

	def _remove_incompatible(self, attack: AttackType, attack_list: List[AttackType]):
		"""
		Removes all the attacks that are incompatible with the specified attack from the specified attack list
		attack: Attack to use for the incompatibility check
		attack_list: List where incompatible attacks will be removed from
		"""
		for attack_in_list in attack_list:
			if not compatible_attacks(attack, attack_in_list):
				attack_list.remove(attack_in_list)

	def _should_stop(self) -> bool:
		"""
		Returns false if the generator should continue its execution or true if it should be stopped
		because its stop flag has been set.
		"""
		return False if self.stop_flag is None else self.stop_flag.is_set()
