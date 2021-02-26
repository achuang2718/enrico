from status_monitor import StatusMonitor
from ionpump import IonPump 
from iongauge import IonGauge
import numpy as np 
import time 

class VacuumMonitor(StatusMonitor):


    """Initialization method.

    Parameters:

    vacuum_instrument_tuple_list: A list of tuples (inst_name, inst_port, inst_type, [inst_read_key1, inst_read_key2, ...], 
                                                    warning_threshold_dict, keyword_dict) 
    Each tuple contains information on a single instrument that the monitor should read. 
        inst_name: str, The (user-generated) name of the instrument which the vacuum monitor should watch 
        inst_port: str, The port name of the instrument
        inst_type: str, a string identifying the type of instrument
            'pump_spc' - A DIGITEL SPC ion pump controller
            'pump_mpc' - A DIGITEL MPC ion pump controller
            'gauge_xgs-600' - An Agilent XGS-600 ion gauge controller
        inst_read_key: A key identifying what values, if any, should be read from the instrument and logged.
            'pressure': Supported for 'pump_spc'
            'voltage': Supported for 'pump_spc'
            'current': Supported for 'pump_spc'
            'pressure1': Supported for 'pump_mpc'.
            'pressure2': Supported for 'pump_mpc'
            'pressurefil1': Supported for 'gauge_xgs-600'
            'pressurefil2': Supported for 'gauge_xgs-600'
            'voltage1', 'voltage2': Supported for 'pump_mpc' 
            'current1, current2': Supported for 'pump_mpc'
        warning_threshold_dict: A dictionary {read_key:Max Value} of combinations of keys and maximum allowed values before a warning is sent
        Keys are all of the values in inst_read_key. May be empty or none. 
        keyword_dict: A dictionary of any keywords that should be passed to the instrument constructor. May be empty.
        
    """
    def __init__(self, instrument_tuple_list, warning_interval_in_min = 10, local_log_filename = "DEFAULT.csv", can_slack_warn = True):
        super().__init__(warning_interval_in_min = warning_interval_in_min, local_log_filename = local_log_filename)
        self.can_slack_warn = can_slack_warn
        self.instrument_list = [] 
        self.instrument_names_list = [] 
        self.instrument_warning_dicts_list = []
        self.instrument_read_keys_list = []
        for instrument_tuple in instrument_tuple_list: 
            inst_name, inst_port, inst_type, inst_read_keys, warning_threshold_dict, keyword_dict = instrument_tuple
            self.instrument_names_list.append(inst_name)
            self.instrument_warning_dicts_list.append(warning_threshold_dict)
            self.instrument_read_keys_list.append(inst_read_keys)
            if(inst_type == 'pump_spc'):
                instrument = IonPump(inst_port, 'spc', inst_port, **keyword_dict)
            elif(inst_type == 'pump_mpc'):
                instrument = IonPump(inst_port, 'mpc', **keyword_dict)
            elif(inst_type == 'gauge_xgs-600'):
                instrument = IonGauge(inst_port, 'xgs-600', **keyword_dict) 
            else:
                raise ValueError("inst_type " + inst_type + " is not supported by vacuum monitor.")
            self.instrument_list.append(instrument) 
        
    def __enter__(self):
        return self 

    def __exit__(self, exc_type, exc_value, traceback):
        for instrument in self.instrument_list:
            instrument.__exit__(exc_type, exc_value, traceback) 

    def monitor_continuously(self, log_local = True, end_time = np.inf):
        start_time = time.time() 
        elapsed_time = 0
        while(elapsed_time < end_time):
            self.monitor_once(log_local = log_local) 
        


    #TODO: Add support for uploading to breadboard
    #TODO: Add support for plotting
    def monitor_once(self, log_local = True):
        overall_dict = {}
        for instrument, instrument_name, instrument_read_keys, warning_threshold_dict in zip(self.instrument_list, self.instrument_names_list, 
                                                                                            self.instrument_read_keys_list, self.instrument_warning_dicts_list):
            instrument_dict = self._monitor_pump_helper(instrument, instrument_name, instrument_read_keys, warning_threshold_dict)
            for key in instrument_dict:
                overall_dict[key] = instrument_dict[key]
        if(log_local):
            self.log_values_locally(overall_dict) 
        return overall_dict

    def _monitor_pump_helper(self, instrument, instrument_name, instrument_read_keys, warning_threshold_dict):
        return_dict = {}
        for instrument_read_key in instrument_read_keys:
            read_value = self._read_helper(instrument, instrument_read_key)
            if(not warning_threshold_dict is None) and (instrument_read_key in warning_threshold_dict):
                threshold = warning_threshold_dict[instrument_read_key] 
                if(read_value > threshold and self.can_slack_warn):
                    self.warn_on_slack("The measured value of " + instrument_read_key + " on " + instrument_name + " was " + str(read_value) + """, 
                    larger than the threshold value of """ + str(threshold) + ".")
            reading_key = instrument_name + " " + instrument_read_key
            return_dict[reading_key] = read_value 
        return return_dict 

            
    def give_instrument_names(self):
        print("This VacuumMonitor instance has the following instruments: ")
        for instrument_name in instrument_names_list:
            print(instrument_name)


    #TODO: Handle exceptions
    @staticmethod
    def _read_helper(instrument, instrument_read_key):
        ION_GAUGE_DELAY = 10
        if(instrument_read_key == "pressure"):
            returned_value = instrument.measure_pressure() 
        elif(instrument_read_key == "pressure1"):
            returned_value = instrument.measure_pressure(1) 
        elif(instrument_read_key == "pressure2"):
            returned_value = instrument.measure_pressure(2) 
        elif(instrument_read_key == "current"):
            returned_value = instrument.measure_current() 
        elif(instrument_read_key == "current1"):
            returned_value = instrument.measure_current(1)
        elif(instrument_read_key == "current2"):
            returned_value = instrument.measure_current(2) 
        elif(instrument_read_key == "voltage"):
            returned_value = instrument.measure_voltage() 
        elif(instrument_read_key == "voltage1"):
            returned_value = instrument.measure_voltage(1) 
        elif(instrument_read_key == "voltage2"):
            returned_value = instrument.measure_voltage(2)
        elif(instrument_read_key == "pressurefil1"):
            instrument.turn_on(1)
            time.sleep(ION_GAUGE_DELAY)
            returned_value = instrument.measure_pressure() 
            instrument.turn_off() 
        elif(instrument_read_key == "pressurefil2"):
            instrument.turn_on(2) 
            time.sleep(ION_GAUGE_DELAY) 
            returned_value = instrument.measure_pressure()
            instrument.turn_off() 
        return returned_value 


