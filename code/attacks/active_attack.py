from attacks.attack_type import AttackType
from attacks.scripts.base_attack import BaseAttack


class ActiveAttack:
	"""
	Represents information about an attack that was started from using attack_tool
	"""

	# Number of the device the attack is being run on
	device_num: int
	# Type of the attack being run
	attack_type: AttackType
	# Attack instance (subclass of BaseAttack), or None if the attack is simulated
	attack: BaseAttack
	# Timestamp of the instant where the attack was started, in ms
	start_time: int

	def __init__(self, device_num: int, attack_type: AttackType, attack: BaseAttack, start_time: int):
		self.device_num = device_num
		self.attack_type = attack_type
		self.attack = attack
		self.start_time = start_time
