import logging
from time import sleep
from dataq_di2008 import Di2008, AnalogPort
import datetime
from status_monitor import StatusMonitor
import sys

TEMPERATURE_THRESHOLD = 50
LOCAL_LOGGING = False
REFERSH_TIME = 10 #seconds
STRIKE_THRESHOLD = 5
my_monitor = StatusMonitor(load_bc=False, local_log_filename='temperatureLogger.csv')
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
sn_1 = '612E65DD'
labels_1 = ['bottom1',
        'bottom2',
        'top1',
        'KSlower1',
        'KSlower2',
        'LiSlower',
        'NaSlower',
        'bottomBucket']
sn_2 = '6124F2DB'
labels_2 = ['pump',
    'feshbachCoil',
    'top2',
    'top3',
    'ByGradient']
thermocouple_type_list = ['j', 'j', 'j', 'j', 'k']
daq_1, port_lookup = initialize_daq(sn_1, labels_1)
daq_2, port_lookup2 = initialize_daq(sn_2, labels_2, thermocouple_type_list=thermocouple_type_list)
port_lookup.update(port_lookup2)
daq_1.start()
daq_2.start()

# wait for values to to start coming in
while not all([port.value for port in port_lookup.values()]):
    sleep(0.1)

strikes = 0
port_overheated = False
while True:
    temperature_dict = {}
    try:
        print(datetime.datetime.now())
        for port in port_lookup.keys():
            port_temperature = port_lookup[port].value
            print([port, port_temperature])
            temperature_dict.update({port: port_temperature})
            if port_temperature > TEMPERATURE_THRESHOLD:
                port_overheated = True
                if strikes > STRIKE_THRESHOLD:
                    my_monitor.warn_on_slack('WARNING: ' + str(port) + ' overheating. Current temperature ' +
                        "{:10.1f} deg C".format(port_temperature), annoying=True)
        if port_overheated:
            strikes += 1
            print('strikes: ', strikes)
        else:
            strikes = 0
            print('strikes reset back to 0.')
        port_overheated = False
        if LOCAL_LOGGING:
            my_monitor.log_values_locally(temperature_dict)
    except:
        error_msg = str('Error: {}. {}, line: {}'.format(
                    sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2].tb_lineno))
        print(error_msg)
#         my_monitor.warn_on_slack('Temperature monitor software error: ' + error_msg)
    sleep(REFRESH_TIME)
# 
