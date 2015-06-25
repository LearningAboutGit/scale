from scale_client.core.application import Application
from scale_client.core.sensed_event import SensedEvent

import time
import copy
from threading import Lock

import logging
log = logging.getLogger(__name__)

class LocationManager(Application):
	"""
	LocationManager collects location information from location providers
	such as GPS, Geo IP service, etc.

	It reports location changes to other components for them to tag SensedEvent
	"""
	def __init__(self, broker, report_update=True, debug=False, debug_interval=10):
		super(LocationManager, self).__init__(broker)

		# Keep location coordinates and its time-stamp, associated with source
		# Format: sensor: {"lat": , "lon": , "alt": , "expire": , "priority": }
		self._location_pool = {}
		self._report_update = report_update
		self._last_value = None
		self._ack_success = False
		self._pool_lock = Lock() # Mutex access to self._location_pool
		self._debug_flag = debug
		self._debug_interval = debug_interval
		self._debug_location_timer = None

	SOURCE_SUPPORT = ["geo_ip", "gps", "fake_location", "rand_location"]

	def on_event(self, event, topic):
		"""
		LocationManager should deal with all location events published by
		location providers.
		"""
		if not self._ack_success:
			ack = SensedEvent(sensor="lman",
					data={"event": "location_manager_ack", "value": self},
					priority=4)
			self.publish(ack)
			log.debug("send ack to event reporter");

		# Ignore events from database
		if hasattr(event, "db_record"):
			return

		# Analyze event
		et = event.get_type()
		data = event.get_raw_data()
		if not et in LocationManager.SOURCE_SUPPORT:
			return
		log.debug("event from " + et)
		#self._publish_debug_text("Received event " + event.to_json())
		item = {
				"lat": data["lat"],
				"lon": data["lon"],
				"alt": None,
				"expire": data["exp"],
				"priority": event.priority
			}
		if "alt" in data:
			item["alt"] = data["alt"]
		self._pool_lock.acquire()
		try:
			#XXX: maybe check if timestamp is newer before update?
			self._location_pool[event.sensor] = item
			self._update_location()
			#self._publish_debug_text("Updated with event from " + et)
		finally:
			self._pool_lock.release()

	def _update_location(self):
		"""
		Remove expired location
		Return location with the highest priority
		"""
		best_device = None
		highest_pri = None
		#log.warning("static debug update location")

		for device in list(self._location_pool):
			if self._location_pool[device]["expire"] < time.time():
				self._location_pool.pop(device, None)
				debug_e = SensedEvent(sensor="lman",
						data={"event": "debug_location_expire", "value": device},
						priority=7
					)
				self.publish(debug_e)
				continue
			if best_device is None or self._location_pool[device]["priority"] < highest_pri:
				best_device = device
				highest_pri = self._location_pool[device]["priority"]

		# if not best_device:
		# 	return
		
		value = None
		#log.warning("static debug device is None: " + str(best_device is None))
		if best_device is not None:
			#log.warning("static debug device: " + str(best_device))
			best_location = self._location_pool[best_device]
			value = {}
			value["lat"] = best_location["lat"]
			value["lon"] = best_location["lon"]
			value["alt"] = best_location["alt"]
		if value is not None and type(value) != type({}): # Should not happedn
			return
		
		# Debug
		self._debug(self._last_value, value)

		if self._last_value is None and value is None:
			return
		if type(self._last_value) != type(value) or self._last_value["lon"] != value["lon"] or self._last_value["lat"] != value["lat"] or (self._last_value["alt"] == self._last_value["alt"] or value["alt"] == value["alt"]) and self._last_value["alt"] != value["alt"]:
			if self._report_update:
				up = SensedEvent(sensor="lman",
						data={"event": "location_update", "value": value},
						priority=8)
				self.publish(up)
		self._last_value = value

	def tag_event(self, event):
		self._ack_success = True
		self._pool_lock.acquire()
		try:
			self._update_location()
		finally:
			self._pool_lock.release()
		if self._last_value is not None:
			event.data["geotag"] = copy.copy(self._last_value)

	def _debug(self, last_value, this_value):
		if not self._debug_flag:
			return
		if (last_value is None) != (this_value is None):
			debug_e = SensedEvent(sensor="lman",
					data={"event": "debug_location_update", "value": this_value is not None},
					priority=7
				)
			self.publish(debug_e)
			#log.warning(this_value is not None)
			self._debug_location_timer = time.time()
		elif self._debug_location_timer is None:
			self._debug_location_timer = time.time()
		elif self._debug_location_timer + self._debug_interval < time.time():
			debug_e = SensedEvent(sensor="lman",
					data={"event": "debug_location_update", "value": this_value is not None},
					priority=7
				)
			self.publish(debug_e)
			#log.warning(this_value is not None)
			self._debug_location_timer = time.time()

	def _publish_debug_text(self, message):
		if not self._debug_flag:
			return
		debug_e = SensedEvent(sensor="lman",
				data={"event": "debug_text", "value": "LM: " + message},
				priority=7
			)
		self.publish(debug_e)

