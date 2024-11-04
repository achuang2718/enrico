import pyvisa
import numpy as np
import pandas as pd
import sys

# Modified from https://gitlab.mpcdf.mpg.de/mpq-polarlab 
# copyright (c) Sebastian Blatt 2015, 2016

class SR760(object):
    # Valid frequency span ids from manual p. 5-4
    FREQUENCY_SPANS = {0: 191e-3,
                        1: 382e-3,
                        2: 763e-3,
                        3: 1.5,
                        4: 3.1,
                        5: 6.1,
                        6: 12.2,
                        7: 24.4,
                        8: 48.75,
                        9: 97.5,
                        10: 195,
                        11: 390,
                        12: 780,
                        13: 1.56e3,
                        14: 3.125e3,
                        15: 6.25e3,
                        16: 12.5e3,
                        17: 25e3,
                        18: 50e3,
                        19: 100e3}

    DISPLAY_UNITS = {0: "Vpk",
                    1: "Vrms",
                    2: "dBV",
                    3: "dBVrms"}

    AVERAGING_TYPES = {0: 'rms',
                        1: 'vector',
                        2: 'peak hold'}

    AVERAGING_MODES = {0: 'lin',
                        1: 'exp'}
    
    N_FREQ_BINS = 400 #Devices takes this number of samples regardless of setting

    def __init__(self, visa_address:str):

        self.rm = pyvisa.ResourceManager()
        self.device = self.rm.open_resource(visa_address)
        self.device.read_termination = '\n'

        self.id = self.device.query('*IDN?')
        print(f'Connected to device with ID: {self.id}')
    
    def close(self):
        self.device.close()
    
    def get_frequency_range(self):
    #Return results of (STRF?, CTRF?, SPAN?) in units of Hz.
        strf = float(self.device.query('STRF?'))
        ctrf = float(self.device.query('CTRF?'))
        span_id = int(self.device.query('SPAN?'))
        span = SR760.FREQUENCY_SPANS[span_id]
        return {'freq_start':strf, 'freq_center':ctrf, 'span':span}

    def get_trace(self, trace_label:int):
        # beware traces start with 0
        if trace_label in [0, 1]:
            level_list = self.device.query(f'SPEC? {trace_label}').split(',')[:self.N_FREQ_BINS]
            level_list = np.array([float(s) for s in level_list])
        else: 
            raise KeyError('Illegal trace number')
        
        freq_range = self.get_frequency_range()

        # freq_list = np.linspace(freq_range['freq_start'], 
        #                         freq_range['span'],
        #                         self.N_FREQ_BINS, 
        #                         endpoint=False)
        freq_list = [float(self.device.query(f'BVAL? {trace_label}, {i}')) for i in range(self.N_FREQ_BINS)]
        
        return {'level_list':level_list, 'freq_list':freq_list}
    
    def save_trace(self, trace_label:int, filename:str):
        trace = pd.DataFrame(self.get_trace(trace_label=trace_label))

        trace.to_csv(filename, index=False)

if __name__ == '__main__':
    sa = SR760(visa_address='ASRL7::INSTR')
    sa.save_trace(filename=str(sys.argv[1]), trace_label=0)
    print('Trace saved. Closing...')
    sa.close()
