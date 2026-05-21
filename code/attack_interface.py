import sys
import time

from attacks.attack_util import *

"""
Interface used to call functions in attack_util through the CLI
Possible usages:
	start <deviceNum> <attackNum>: Flags the start of an attack
	end <deviceNum> <attackNum> <startTime>: Flags the end of an attack
		<startTime> is the start time of the attack specified as a UNIX timestamp in miliseconds
"""


def main():
	args = sys.argv
	if args[1] == "start":
		return flag_attack_start(int(args[1]), int(args[2]))
	elif args[1] == "end":
		return flag_attack_end(int(args[1]), int(args[2]), int(args[3]), int(time.time() * 1000))
	else:
		return -1


if __name__ == "__main__":
	main()
