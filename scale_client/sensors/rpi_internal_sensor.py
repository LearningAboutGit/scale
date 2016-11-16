from scale_client.sensors.virtual_sensor import VirtualSensor
import psutil

import logging
log = logging.getLogger(__name__)

class RPiInternalSensor(VirtualSensor):
    def __init__(self, broker, device=None, interval=1):
        super(RPiInternalSensor, self).__init__(broker, device=device, interval=interval)
	DEFAULT_PRIORITY = 7
        
    def get_type(self):
	return "rpi"
      
    def read_raw(self):
      	#read CPU temperature of raspberry pi
      	with open("/sys/class/thermal/thermal_zone0/temp") as f:
            data = f.read().rstrip()
        #read memory usage status
        data += " RAM %" + str(psutil.virtual_memory()[2])
      	return data
      	#return psutil.virtual_memory()
      
    #def policy_check(self):
    #  	return False 
