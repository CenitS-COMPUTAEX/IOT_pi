import socket
import time
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import wait
from threading import Thread
from typing import List

from attacks.scripts.base_attack import BaseAttack
from defs.remote import Remote
from defs.utils import log
from defs.config import Config as Cfg


class PortScanAttack(BaseAttack):
	"""
	Attack that checks which ports are open on the target host.
	"""
	config: Cfg
	active: bool
	stop_flag: bool
	target_ip: str

	def __init__(self):
		self.active = False
		self.stop_flag = False
		self.config = Cfg.get()

	def is_synchronous(self) -> bool:
		return False

	def get_attack_name(self) -> str:
		return "Port scan"

	def start(self, device_num: int) -> bool:
		self.target_ip = Remote.get_ip(device_num)

		self.stop_flag = False
		self.active = True

		Thread(target=self.run).start()

		return True

	def run(self):
		with ThreadPoolExecutor() as executor:
			futures = []
			for task_num in range(self.config.port_scan_num_threads):
				# Evenly split all ports among the different threads
				futures.append(executor.submit(
					self.loop, [i for i in range(task_num, 65536, self.config.port_scan_num_threads)]))
			wait(futures)
		self.active = False

	def loop(self, ports: List[int]):
		"""
		Checks all the ports on the list to determine if they are open or not.
		Does not stop until the stop flag is set.
		"""
		while True:
			for port in ports:
				if self.stop_flag:
					return

				with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
					s.settimeout(self.config.port_scan_timeout)
					try:
						s.connect((self.target_ip, port))
						# Port open
					except (ConnectionError, TimeoutError):
						# Port closed
						pass

				if self.config.port_scan_delay > 0 and not self.stop_flag:
					time.sleep(self.config.port_scan_delay)

	def end(self):
		self.stop_flag = True
		# Wait until the current iteration of the script ends
		log("Waiting for port scan script to finish...")
		while self.active:
			time.sleep(0.1)
