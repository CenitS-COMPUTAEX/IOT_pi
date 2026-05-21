"""
Custom exceptions
"""


class IllegalOperationError(Exception):
	pass


class ConfigurationError(Exception):
	"""
	Thrown when the configuration passed to the program is invalid or incorrect
	"""
	pass
