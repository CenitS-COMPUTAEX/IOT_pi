from attacks.scripts.mining_attack import MiningAttack


class LiteMiningAttack(MiningAttack):
	"""
	Lite version of the mining attack that only uses 2 threads for mining
	"""

	def get_attack_name(self) -> str:
		return "Lite mining"

	# Arguments to pass to the mining program
	MINER_ARGS = "--benchmark --cpu-priority 2 -t 2"
