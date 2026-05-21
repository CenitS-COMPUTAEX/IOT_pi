class EventTime:
	"""
	Contains relevant timestamps for an attack event
	"""

	# All timestamps are stored in seconds

	# Timestamp of the start of the event list
	list_start_time: float
	# Timestamp when the event should take place
	event_time: float

	# Offset between list_start_time and event_time, but represented in hours, minutes, and seconds.
	offset_hours: int
	offset_minutes: int
	offset_seconds: float

	def __init__(self, list_start_time: float, event_time: float):
		self.list_start_time = list_start_time
		self.event_time = event_time

		offset = self.event_time - self.list_start_time

		self.offset_hours = int(offset // 3600)
		offset -= self.offset_hours * 3600
		self.offset_minutes = int(offset // 60)
		offset -= self.offset_minutes * 60
		self.offset_seconds = offset

	def get_offset_str(self) -> str:
		"""
		Returns the offset between the generation time and event time, with hh:mm:ss format.
		"""
		ret = "+"
		ret += "%02i" % self.offset_hours
		ret += ":"

		ret += "%02i" % self.offset_minutes
		ret += ":"

		ret += "%06.3f" % self.offset_seconds

		return ret
