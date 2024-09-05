"""
Script for interfacing HP 8561B spectrum analyzer
Modified from https://github.com/sixtemesseven/visa-instruments
"""

import pyvisa
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import animation 
import string
import math
import cmath
import time
# from skrf import Network, Frequency
from mpl_toolkits.mplot3d import Axes3D

        
        
class HP8561B(object):
    '''
    classdocs
    This class provides an easy interface to the HP856xEC spectrum analyzer.
    It should also work with with other HP analyzers (untested)
    '''

    def __init__(self, bus, addr):
        '''
        Initiate GPIB instance
        '''
        self.visaID = 'GPIB' + str(bus) + '::' + str(addr) + '::INSTR'
        self.rm = pyvisa.ResourceManager()
        self.instance = self.rm.open_resource(str(self.visaID))
        self.instance.read_termination = '\n'
    def commandInstrument(self, command):
        '''
        Send a GPIB command to instrument
        Raises exception if the device is unreachable
        '''
        code = self.instance.write(str(command))

    def queryInstrument(self, request):
        '''
        Query GPIB Device
        '''
        return(self.instance.query(str(request)))

    def setSpan(self, span, unit = 'Hz'):
        '''
        set frequency span of spectrum analyzer in (float) MHz
        '''
        command = f'SP {span}' + unit
        self.commandInstrument(command)
        print(command)

    def get_span(self):
        """
        query span in Hz
        """
        return float(self.queryInstrument('SP?'))

    def setCenter(self, center, unit):
        '''
        set center frequency of spectrum analyzer in (float) MHz
        '''
        command = f'CF {center}' + unit
        self.commandInstrument(command)
        print(command)

    def get_center(self):
        """query center in Hz"""
        return float(self.queryInstrument('CF?'))
    
    def get_start_freq(self):
        """query start frequency in Hz"""
        return float(self.queryInstrument('FA?'))

    def get_end_freq(self):
        """query end frequency in Hz"""
        return float(self.queryInstrument('FB?'))

    def setExternalRef(self, external=None):
        '''
        set external reference (True) or internal Reference (False), returns INTernal or EXTernal
        '''
        if external is None:
            external = True
        if external:
            self.commandInstrument('FREF EXT')
        else:
            self.commandInstrument('FREF INT')
        return(self.queryInstrument('FREF?'))

    def setRBW(self, RBW=None, unit='Hz'):
        '''
        Set resolution bandwith manual in MHz or to auto rbw (float) (default=Auto)
        '''
        if RBW is not None:
            command = f'RB {RBW}'+unit
        else:
            command = 'RB AUTO'
        self.commandInstrument(command)
        print(command)
    
    def get_rbw(self):
        """
        query rbw in Hz
        """
        return float(self.queryInstrument('RB?'))

    def setTitle(self, text):
        '''
        Writes a title on top of the sa display and vga output
        '''
        self.commandInstrument('TITLE' + text)

    def getMarker(self, text):
        '''
        Writes a title on top of the sa display and vga output
        '''
        self.commandInstrument('TITLE' + text)

    def get_trace(self, trace_label:str):
        '''
        return 
        '''
        level_list = self.queryInstrument(f'TR{trace_label}?').split(',')
        for i in range(len(level_list)):
            level_list[i] = float(level_list[i])

        (freq_start, freq_end, rbw) = (self.get_start_freq(), self.get_end_freq(), self.get_rbw())
        freq_list = np.linspace(freq_start,freq_end, 601)
        trace_dict = {'frequency_list':freq_list, 'level_list':level_list, 'rbw':rbw}

        return(trace_dict)

    def get_and_show_trace(self, trace_label:str):
        '''
        Shows a graph with the current spectrum analyzer measurments
        '''
        trace_dict = self.get_trace(trace_label=trace_label)
        x_list = trace_dict['frequency_list']
        y_list = trace_dict['level_list']
        rbw = trace_dict['rbw']
        # plt.scatter(x_list, y_list, s=1)
        plt.plot(x_list, y_list, color='red')
        plt.xlabel('Frequency [Hz]')
        plt.ylabel('Level [dBm]')
        plt.title('HP8561B SA Measurment')
        plt.grid()
        plt.show()

    def monitor(self, persistance=None):
        '''
        Shows and overdraws measurments from the spectrum analyzer as it updates

        Keywords:
        persistance = overlays graphs continiously when on (bool) (Default=OFF)
        '''
        xAxis = []
        for i in range(601):
            xAxis.append(i)

        self.fig = plt.figure()

        plt.xlabel('Center Frequency +/- 600 Points')
        plt.ylabel('Amplitude [dB]')
        plt.title('HP8562 SA Measurment')
        plt.grid()

        def animate(i):
            if persistance is None:
                plt.clf()
            self.list = self.getMeasurmentList()
            plt.scatter(xAxis, self.list, s=1)
            self.line = plt.plot(xAxis, self.list)

        self.ani = animation.FuncAnimation(self.fig, animate, interval=10)
        plt.show()
        

 
        
            
            
        
