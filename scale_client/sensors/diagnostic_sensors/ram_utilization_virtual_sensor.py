from scale_client.sensors.virtual_sensor import VirtualSensor
import psutil

import logging
log = logging.getLogger(__name__)

class RAMUtilizationVirtualSensor(VirtualSensor):
    def __init__(self, broker, device=None, interval=1, threshold=60.0):
        super(RAMUtilizationVirtualSensor, self).__init__(broker, device=device, interval=interval)
	self._threshold = threshold;

	DEFAULT_PRIORITY = 7
        
    def get_type(self):
	return "ram_utilization"
      
    def read_raw(self):
        #read memory usage status
        data = "RAM %" + str(psutil.virtual_memory()[2])
      	return data 
