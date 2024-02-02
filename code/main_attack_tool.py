"""
Main script that can be used to run an instance of AttackTool, which allows starting and stopping attacks
through user input.
"""
import sys

from attacks.attack_type import AttackType
from attacks.attack_tool import AttackTool


def print_help(real_attacks: bool):
	mode_str = "(Real attacks mode)" if real_attacks else "(Simulation mode)"
	print("- Attack script " + mode_str + " -\n"
		"help: Prints this help\n"
		"start <deviceNum> <attackNum | attackName>: Starts an attack. If the attack is synchronous, it will wait until "
		"it's over before returning.\n"
		"end|stop <deviceNum> <attackNum | attackName>: Ends an asynchronous attack\n"
		"list: Lists active attacks\n"
		"endall: Stops all attacks\n"
		"clean: Deletes all attack files that might be present as a leftover. Can only be run if there's no active attacks.\n"
		"quit (or Ctrl+C): Stops all attacks and quits\n"
		"Possible values for attackName:\n"
		"  mining (0) (async): Cryptocurrency mining attack\n"
		"  login (1) (async): Brute force login attack\n"
		"  crypt (2) (async): File encryption attack\n"
		"  pass (3) (async): Password guessing attack\n"
		"  lite-mining (4) (async): Cryptocurrency mining attack (only 2 threads)\n"
		"  test (5) (sync): Synchronous attack test")
	if not real_attacks:
		print("Launch with -r flag to enable real attacks")


def main():
	args = sys.argv

	# Parse flags first
	real_attacks = False
	if "-r" in args:
		args.remove("-r")
		real_attacks = True

	attack_tool = AttackTool(real_attacks)

	print_help(real_attacks)
	while True:
		try:
			input_data = input().split(" ")

			if input_data[0] == "start":
				error = False
				attack = None
				try:
					attack = AttackType.from_str(input_data[2])
				except ValueError:
					print_help(real_attacks)
					error = True
				if not error:
					attack_tool.start_attack(int(input_data[1]), attack)
			elif input_data[0] == "end" or input_data[0] == "stop":
				error = False
				attack = None
				try:
					attack = AttackType.from_str(input_data[2])
				except ValueError:
					print_help(real_attacks)
					error = True
				if not error:
					attack_tool.end_attack(int(input_data[1]), attack)
			elif input_data[0] == "list":
				attack_tool.list_attacks()
			elif input_data[0] == "endall":
				attack_tool.end_all_attacks()
			elif input_data[0] == "clean":
				attack_tool.clean_attack_files()
			elif input_data[0] == "quit":
				attack_tool.end_all_attacks()
				exit(0)
			else:
				print_help(real_attacks)
		except KeyboardInterrupt:
			attack_tool.end_all_attacks()
			exit(0)


if __name__ == "__main__":
	main()
