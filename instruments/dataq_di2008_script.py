import logging
from time import sleep
from dataq_di2008 import Di2008, AnalogPort
import datetime
from status_monitor import StatusMonitor
import sys

TEMPERATURE_THRESHOLD = 50
my_monitor = StatusMonitor()
logging.basicConfig(level=logging.DEBUG)

def initialize_daq(serial_number_str, labels, thermocouple_type_list=None):
    daq = Di2008(serial_number = serial_number_str)
    if thermocouple_type_list is None:
        thermocouple_type_list = ['k'] * len(labels)
    port_lookup = {labels[i] : AnalogPort(i+1, thermocouple_type=thermocouple_type_list[i])
        for i in range(len(labels))}
    daq.create_scan_list([port for port in port_lookup.values()])
    return daq, port_lookup

#Initialize DAQs and define settings
# sn_1 = '612E65DD'
# labels_1 = ['bottom1',
#         'bottom2',
#         'top1',
#         'KSlower1',
#         'KSlower2',
#         'LiSlower',
#         'NaSlower',
#         'bottomBucket']
# daq_1, port_lookup = initialize_daq(sn_1, labels_1)
port_lookup = {}


sn_2 = '6124F2DB'
labels_2 = ['pump',
    'feshbachCoil',
    'top2',
    'top3',
    'ByGradient']
thermocouple_type_list = ['j', 'j', 'j', 'j', 'k']
daq_2, port_lookup2 = initialize_daq(sn_2, labels_2, thermocouple_type_list=thermocouple_type_list)
port_lookup.update(port_lookup2)
# daq_1.start()
daq_2.start()

# wait for values to to start coming in
while not all([port.value for port in port_lookup.values()]):
    sleep(0.1)

while True:
    try:
        print(datetime.datetime.now())
        for port in port_lookup.keys():
            port_temperature = port_lookup[port].value
            print([port, port_temperature])
            if port_temperature > TEMPERATURE_THRESHOLD:
                my_monitor.warn_on_slack('WARNING: ' + str(port) + ' overheating. Current temperature ' +
                    "{:10.1f} deg C".format(port_temperature), annoying=True)
    except:
        error_msg = str('Error: {}. {}, line: {}'.format(
                    sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2].tb_lineno))
        # my_monitor.warn_on_slack('Temperature monitor software error: ' + error_msg)
    sleep(2)

