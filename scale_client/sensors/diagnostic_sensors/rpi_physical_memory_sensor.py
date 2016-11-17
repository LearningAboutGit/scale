from scale_client.sensors.virtual_sensor import VirtualSensor
import psutil

import logging
log = logging.getLogger(__name__)

class RPiMemoryVirtualSensor(VirtualSensor):
    def __init__(self, broker, device=None, interval=1):
        super(RPiMemoryVirtualSensor, self).__init__(broker, device=device, interval=interval)
	DEFAULT_PRIORITY = 7
        
    def get_type(self):
	return "physical_memory_free"
      
    def read_raw(self):
        #read memory usage status
        data = "FREE PHYSICAL MEMORY %" + str(psutil.virtual_memory()[2])
      	return data 
