import xml.etree.ElementTree as ElementTree

from typing import List
from xml.etree.ElementTree import Element

from attacks.attack_type import AttackType
from defs.exceptions import ConfigurationError

# Config file location
CONFIG_FILE = "Config.xml"

# Singleton instance
_instance = None


class Config:
	"""
	Class that contains user-specified configuration data for the program. The config is stored in an XML file.
	This class works as a singleton.
	"""

	# List of device connection data. Each element contains another list with 3 elements: IP, username and password.
	device_conn_data: List[List[str]]
	# Max number of seconds to wait for when connecting to remote devices
	connection_timeout: int
	# Max number of connection tries when connecting to remote devices
	max_connection_tries: int
	# Files used for the mining attack
	mining_file_to_send: str  # Empty string if multiple files are sent instead
	mining_files_to_send: List[str]  # None if multiple files are sent instead
	mining_remote_file: str
	# Number of threads to use for the login attack
	login_num_threads: int
	# Files used for the encryption attack
	encryption_file_to_send: str  # Empty string if multiple files are sent instead
	encryption_files_to_send: List[str]  # None if multiple files are sent instead
	encryption_remote_file: str
	encryption_folder_to_encrypt: str
	# Minimum duration for the encryption attack
	encryption_min_duration: int
	# Max amount of seconds to wait for the encryption attack to end
	encryption_wait_timeout: int
	# Files used for the password attack
	pass_remote_file: str
	# Command to use to launch python on the remote device
	remote_python_command: str
	# Power measurement delay
	measurement_delay: float

	def __init__(self):
		"""
		Creates a new instance by reading the config file
		"""
		root = ElementTree.parse(CONFIG_FILE).getroot()

		devices_element = root.find("Devices")
		self.device_conn_data = []
		for device_element in devices_element.findall("Device"):
			self.device_conn_data.append([device_element.find("IP").text, device_element.find("Username").text,
				device_element.find("Password").text])

		self.connection_timeout = int(root.find("ConnectionTimeout").text)
		self.max_connection_tries = int(root.find("ConnectionTries").text)

		attacks_element = root.find("Attacks")

		mining_element = attacks_element.find("Mining")
		self._set_files_to_send(mining_element, AttackType.MINING)
		self.mining_remote_file = mining_element.find("RemoteFile").text

		login_element = attacks_element.find("Login")
		self.login_num_threads = int(login_element.find("NumThreads").text)

		encryption_element = attacks_element.find("Encryption")
		self._set_files_to_send(encryption_element, AttackType.ENCRYPTION)
		self.encryption_remote_file = encryption_element.find("RemoteFile").text
		self.encryption_folder_to_encrypt = encryption_element.find("FolderToEncrypt").text
		self.encryption_min_duration = int(encryption_element.find("MinDuration").text)
		self.encryption_wait_timeout = int(encryption_element.find("WaitTimeout").text)

		pass_element = attacks_element.find("Pass")
		self.pass_remote_file = pass_element.find("RemoteFile").text

		self.remote_python_command = root.find("RemotePythonCommand").text
		self.measurement_delay = float(root.find("MeasurementDelay").text)

	@classmethod
	def get(cls):
		"""
		Returns an instance of this class. The instance will always be unique: once instantiated, no more copies
		will be created.
		"""

		global _instance
		if _instance is None:
			_instance = cls()
		return _instance

	def get_file_to_send(self, attack: AttackType, device_num: int) -> str:
		"""
		Given an attack type and a device number, returns the name of the file that needs to be sent to said device
		to launch the specified attack.
		If the attack does not require sending a file, throws ValueError.
		"""
		if attack == AttackType.ENCRYPTION:
			if self.encryption_file_to_send != "":
				return self.encryption_file_to_send
			elif self.encryption_files_to_send is not None:
				return self.encryption_files_to_send[device_num - 1]
		elif attack == AttackType.MINING:
			if self.mining_file_to_send != "":
				return self.mining_file_to_send
			elif self.mining_files_to_send is not None:
				return self.mining_files_to_send[device_num - 1]
		else:
			raise ValueError("Attack " + attack.name + " does not require sending a file.")

	def _set_files_to_send(self, parent_element: Element, attack: AttackType):
		"""
		Given a config XML element that might contain child <FileToSend> and <FilesToSend> tags, sets the appropriate
		"file_to_send" or "files_to_send" variable.
		If both or neither of the tags are present in the element, throws ConfigurationError
		If the attack does not have a "File(s)ToSend" configuration value, throws ValueError
		"""
		parent_element_name = parent_element.tag

		file_element = parent_element.find("FileToSend")
		files_element = parent_element.find("FilesToSend")
		if file_element is not None:
			if files_element is None:
				file_to_send = file_element.text
				files_to_send = None
			else:
				raise ConfigurationError("\"" + parent_element_name + " > FileToSend\" and \"" + parent_element_name +
					" > FilesToSend\" tags can't be specified at the same time. If you want to use the same binary "
					"for all end devices, comment out <FilesToSend>. If you want to use a different binary for each "
					"one, comment out <FileToSend>.")
		else:
			if files_element is not None:
				files_to_send = [elem.text for elem in files_element.findall("file")]
				file_to_send = ""
			else:
				raise ConfigurationError("Either \"" + parent_element_name + " > FileToSend\" or \"" +
					parent_element_name + " > FilesToSend\" must be specified.")

		# Set the corresponding variable depending on the attack
		if attack == AttackType.ENCRYPTION:
			self.encryption_file_to_send = file_to_send
			self.encryption_files_to_send = files_to_send
		elif attack == AttackType.MINING:
			self.mining_file_to_send = file_to_send
			self.mining_files_to_send = files_to_send
		else:
			raise ValueError("Attack " + attack.name + " does not have a File(s)ToSend config value.")
