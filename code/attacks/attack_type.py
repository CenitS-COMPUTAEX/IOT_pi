from enum import Enum


class AttackType(Enum):
	"""
	Represents the different kinds of attack that can be run. Each one has an unique number associated to it.
	"""
	MINING = 0       # Joint representation: 1
	LOGIN = 1        # Joint representation: 2
	ENCRYPTION = 2   # Joint representation: 4
	PASSWORD = 3     # Joint representation: 8
	LITE_MINING = 4  # Joint representation: 16
	TEST = 5         # Joint representation: 32

	@classmethod
	def from_str(cls, string: str):
		"""
		Given a string that contains the short name of the attack, or an integer representing an attack, returns the
		corresponding enum value.
		If the input doesn't represent a valid attack type, throws ValueError.
		"""
		val_int = None
		try:
			val_int = int(string)
		except ValueError:
			pass

		if val_int is None:
			# It's probably specified as a name
			if string == "mining":
				return cls.MINING
			elif string == "login":
				return cls.LOGIN
			elif string == "crypt":
				return cls.ENCRYPTION
			elif string == "pass":
				return cls.PASSWORD
			elif string == "lite-mining":
				return cls.LITE_MINING
			elif string == "test":
				return cls.TEST
			else:
				raise ValueError("Unrecognized attack type: " + string)
		else:
			return cls(val_int)
