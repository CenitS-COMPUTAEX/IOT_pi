import random
import string
import time
import hashlib

"""
Test attack file that tries to guess a SHA-256 hashed password through brute force.
Keeps running even if it somehow manages to guess the password.
The attack will sleep at random time intervals.
"""

# Brute force guess chance: 1/390877006486250192896
PASSWORD_TO_GUESS = "anWKQlssBVpF"


def main():
	print("Starting SHA calculation script")
	hash_to_guess = hashlib.sha256(bytes(PASSWORD_TO_GUESS, "ASCII"))
	while True:
		time_end = time.time() + random.uniform(3, 6)
		while time.time() < time_end:
			# Perform several more guesses before checking the time again
			for _ in range(500):
				# Try to guess the password
				random_str = ''.join(random.choice(string.ascii_lowercase + string.ascii_uppercase)
					for _ in range(len(PASSWORD_TO_GUESS)))

				if hashlib.sha256(bytes(random_str, "ASCII")) == hash_to_guess:
					print("Password guessed")

		# Sleep for a bit before continuing
		time.sleep(random.uniform(2, 4))


if __name__ == "__main__":
	main()
