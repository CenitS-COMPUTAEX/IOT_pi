from attacks.attack_type import AttackType
from attacks.scripts.encryption_attack import EncryptionAttack
from attacks.scripts.login_attack import LoginAttack
from attacks.scripts.lite_mining_attack import LiteMiningAttack
from attacks.scripts.mining_attack import MiningAttack
from attacks.scripts.password_guess_attack import PasswordGuessAttack
from attacks.scripts.test_attack import TestAttack


class AttackFactory:
	"""
	Class used to instantiate attacks given an AttackType
	"""

	def get_attack(self, attack: AttackType):
		if attack == AttackType.MINING:
			return MiningAttack()
		if attack == AttackType.LOGIN:
			return LoginAttack()
		elif attack == AttackType.ENCRYPTION:
			return EncryptionAttack()
		elif attack == AttackType.PASSWORD:
			return PasswordGuessAttack()
		elif attack == AttackType.LITE_MINING:
			return LiteMiningAttack()
		elif attack == AttackType.TEST:
			return TestAttack()
		else:
			raise NotImplementedError("Attack type " + attack.name + " has not been implemented")
