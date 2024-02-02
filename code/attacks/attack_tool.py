import time
from typing import List
from datetime import datetime

import attacks.attack_util as attack_util
from attacks.attack_util import Status
from defs.exceptions import IllegalOperationError
from attacks.active_attack import ActiveAttack
from attacks.attack_type import AttackType
from attacks.attack_factory import AttackFactory
from defs.constants import Constants as Cst
from defs.utils import log


class AttackTool:
	"""
	Main attack script. Allows starting both fake and real attacks.
	Sets the individual attack flags that are checked by the main loop.
	"""

	# Lists all attacks started by this script
	# Each element contains an instance of ActiveAttack
	current_attacks: List[ActiveAttack] = []

	real_attacks: bool

	def __init__(self, real_attacks: bool):
		self.real_attacks = real_attacks

	def start_attack(self, device_num: int, attack_type: AttackType):
		if self.get_attack_list_entry(device_num, attack_type) is None:
			# Ensure there's not another attack that is incompatible with this one running on the same device
			preventing_attack = self._check_compatibility(device_num, attack_type)
			if preventing_attack is None:
				result = attack_util.flag_attack_start(device_num, attack_type.value)

				if result == Status.SUCCESS:
					attack = self.get_attack_instance(attack_type)
					self.current_attacks.append(ActiveAttack(device_num, attack_type, attack, int(time.time() * 1000)))
					if self.real_attacks:
						log("Starting attack " + attack_type.name + " on device " + str(device_num) + "...")
						result = attack.start(device_num)
						if result:
							if attack.is_synchronous():
								# If the attack is synchronous, attack.start() won't return until it's over.
								# We automatically stop it once that happens.
								self.end_attack(device_num, attack_type)
							else:
								# If the attack is asynchronous, attack.start() returns as soon as the attack is started.
								# Notify the user about that.
								log("Attack " + attack_type.name + " on device " + str(device_num) + " started")
						else:
							# The attack failed to start correctly, end it immediately to prevent corrupting the
							# dataset if one is being created
							log("Attack " + attack_type.name + " on device " + str(device_num) + " couldn't be "
								"started. Flagging it as ended...")
							self.end_attack(device_num, attack_type)
							log("If a dataset was being created, some incorrect instances have been introduced as a "
								"result of this, since the attack wasn't actually run.")
					else:
						log("Simulation of attack " + attack_type.name + " on device " + str(device_num) + " started")
				elif result == Status.ERROR_ATTACK_FILE_ALREADY_EXISTS:
					log("Error: Attack " + attack_type.name + " is already active on device " + str(device_num) +
						" (started by another script)")
				elif result == Status.OS_ERROR:
					log("Error: Could not create attack file")
			else:
				log("Error: Attack " + attack_type.name + " and attack " + preventing_attack.name + " cannot be "
					"active at the same time on the same device")
		else:
			log("Error: Attack " + attack_type.name + " is already active on device " + str(device_num))

	def end_attack(self, device_num: int, attack_type: AttackType):
		attack_entry = self.get_attack_list_entry(device_num, attack_type)

		if attack_entry is not None:
			# Check if the attack can be ended first
			if self.can_end_attack(attack_entry):
				# Try to end the attack if it's not a simulation
				if self.real_attacks:
					try:
						attack_entry.attack.end()
					except IllegalOperationError:
						log("Warning: Attack " + attack_type.name + " is synchronous and cannot be ended early. "
							"The attack will be marked as ended, but the attack script will continue running until "
							"it ends.")

				# Try to flag the attack as ended
				result = attack_util.flag_attack_end(device_num, attack_type.value, attack_entry.start_time,
					int(time.time() * 1000))

				if result == Status.SUCCESS:
					log("Attack " + attack_type.name + " on device " + str(device_num) + " stopped")
				else:
					log("Error: Could not delete attack file and/or log attack data")
				self.delete_attack_list_entry(device_num, attack_type)
			else:
				# The attack cannot be marked as ended. We try to end it anyway, in case it's still running.
				self.delete_attack_list_entry(device_num, attack_type)
				if self.real_attacks:
					try:
						attack_entry.attack.end()
					except IllegalOperationError:
						pass
		else:
			log("Error: Attack " + attack_type.name + " is not active on device " + str(device_num))

	def can_end_attack(self, attack: ActiveAttack) -> bool:
		"""
		Checks if an attack can be ended and displays the corresponding error messages if it can't.
		Returns true if the attack can be ended, false otherwise.
		"""
		result = attack_util.can_end_attack(attack.device_num, attack.attack_type.value)
		if result == Status.SUCCESS:
			return True
		else:
			if result == Status.ERROR_ATTACK_FILE_DOES_NOT_EXIST:
				log("Error: Attack " + attack.attack_type.name + " on device " +
					str(attack.device_num) + " is marked as active on the program, but the attack file " +
					"can't be found.\n" +
					"The attack won't be logged and will be maked as inactive.")
			else:
				log("Error: Attack " + attack.attack_type.name + " on device " + str(attack.device_num) +
					" cannot be ended for some unknown reason.")
			return False

	def list_attacks(self):
		print("Active attacks:")
		for entry in self.current_attacks:
			print("- Type: " + entry.attack_type.name + ", device: " + str(entry.device_num) + ", time started: " +
				datetime.fromtimestamp(entry.start_time / 1000).strftime('%Y-%m-%d %H:%M:%S'))

	def end_all_attacks(self):
		while len(self.current_attacks) > 0:
			entry = self.current_attacks[0]
			self.end_attack(entry.device_num, entry.attack_type)

	def clean_attack_files(self):
		"""
		Deletes all the attack files that might be present as a leftover from a previous run that failed.
		Can only be run if there's no active attacks.
		"""
		if len(self.current_attacks) == 0:
			result = attack_util.delete_all_attack_files()
			if result == Status.SUCCESS:
				log("Deleted all leftover attack files")
			elif result == Status.OS_ERROR:
				log("Error: Could not delete attack files")
		else:
			log("Error: Attack list can only be cleaned if there are no active attacks")

	def get_attack_instance(self, attack_type: AttackType):
		"""
		Returns the instance that should be stored in the active attacks array when a new attack is started.
		If the real_attacks flag is set, returns the proper attack instance. If not, returns None.
		"""
		if self.real_attacks:
			return AttackFactory().get_attack(attack_type)
		else:
			return None

	def get_attack_list_entry(self, device_num: int, attack_type: AttackType) -> "ActiveAttack | None":
		"""
		Returns the attack entry in the active attacks list identified by the specified device and attack type.
		If an entry identified by those numbers isn't found, returns None.
		"""
		for entry in self.current_attacks:
			if entry.device_num == device_num and entry.attack_type == attack_type:
				return entry
		return None

	def delete_attack_list_entry(self, device_num: int, attack_type: AttackType):
		"""
		Deletes the attack entry from the active attacks list identified by the specified device and attack number
		"""
		for entry in self.current_attacks:
			if entry.device_num == device_num and entry.attack_type == attack_type:
				self.current_attacks.remove(entry)

	def _check_compatibility(self, device_num: int, attack_to_start: AttackType) -> "AttackType | None":
		"""
		Given the type of an attack to start and the device where it's going to be started, checks if it's
		incompatible with any of the attacks that are already running on that device.
		device_num: Number of the device where the attack is about to be started
		attack_to_start: Type of the attack that is about to be started
		return: If the attack can be started, returns None. Otherwise, returns the type of the attack that prevents
		the new attack from being started.
		"""
		for pair in Cst.INCOMPATIBLE_ATTACKS:
			try:
				attack_to_start_pos = pair.index(attack_to_start)
			except ValueError:
				attack_to_start_pos = -1

			if attack_to_start_pos != -1:
				other_attack = pair[1 if attack_to_start_pos == 0 else 0]
				# Check if the other attack is already active on this device
				current_entry = self.get_attack_list_entry(device_num, other_attack)
				if current_entry is not None:
					return current_entry.attack_type
		return None
