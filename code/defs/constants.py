"""
File used to store global constants.
"""
from attacks.attack_type import AttackType


class Constants:
	# Folder where attack files are stored
	ATTACK_FOLDER = "data/attacks"
	# Prefix of the name used for active attack files
	ATTACK_FILE_PREFIX = "attack-"
	# Keyword written to a prediction buffer to signal that the execution is over
	BUFFER_OVER_KEYWORD = "END"

	# Contains a list of attack pairs that can't be run at the same time
	INCOMPATIBLE_ATTACKS = [
		[AttackType.MINING, AttackType.LITE_MINING]
	]
