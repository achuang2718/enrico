import pyvisa
import time

rm = pyvisa.ResourceManager()
device = rm.open_resource('ASRL5::INSTR')
device.baud_rate = 19200 # must be this value
device.read_termination = '\r\n'
device.write_termination = None

def extract_data(response:str):
    """
    Semi-hardcoded. Tested only for temperature, resistance, and device id.
    """
    return response.strip()[9:17]

for i in range(10):
    response = str(device.query('!101101+000.00024'))
    print(response)
    breakpoint()
    print(extract_data(response))
    time.sleep(1)
    
device.close()