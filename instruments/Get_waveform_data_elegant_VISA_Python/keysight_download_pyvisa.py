# import usbtmc
import pyvisa
import numpy as np
import sys
import matplotlib.pyplot as plt
# if len(sys.argv) < 3:
#     print('Usage: python keysight_download.py [channel list] [output filename (.csv)]')
#     exit(-1)

visa_address = 'TCPIP0::192.168.1.3::INSTR'
rm = pyvisa.ResourceManager()
scope = rm.open_resource(visa_address)
scope.timeout = 3000
scope.read_termination = '\n'
scope.write_termination = '\n'
chan_string = '1,3'
filename = 'test.csv'





idn = scope.query('*IDN?')
print('Found scope with IDN {}'.format(idn))

# Setting waveform format to word
scope.write(':WAV:FORM WORD')
# Setting waveform byte order to LSB
scope.write(':WAV:BYT LSB')
# Setting waveform points mode to max
scope.write(':WAV:POIN:MODE MAX')
# Setting waveform points to max
scope.write(':WAV:POIN MAX')
# Setting waveform count to 1
scope.write(':WAV:COUN 1')
# Setting waveform type to normal
scope.write(':WAV:TYPE NORM')
# Setting waveform to unsigned
scope.write(':WAV:UNS 1')

print('Stopping scope')
scope.write(':STOP')

# Build timebase
xinc = float(scope.query(':WAV:XINC?'))
xor = float(scope.query(':WAV:XOR?'))
points = int(scope.query(':WAV:POIN?'))

t = np.arange(points) * xinc + xor

# chan_list = sys.argv[1].split(',')
chan_list = chan_string.split(',')

all_data = np.zeros((points, len(chan_list)+1))
all_data[:,0] = t

for i, chan in enumerate(chan_list):
    print('Setting channel')
    scope.write(':WAV:SOUR CHAN{}'.format(chan))

    yinc = float(scope.query(':WAV:YINC?'))
    yor = float(scope.query(':WAV:YOR?'))
    yref = float(scope.query(':WAV:YREF?'))
    print('Reading data')
    scope.write(':WAV:DATA?')
    data = scope.read_raw()
    # Strip preamble
    if chr(data[0]) != '#':
        print('Corrupted data')
        break
    preamble_len = int(chr(data[1]))
    data = data[preamble_len + 2:-1]
    data_arr = np.frombuffer(data, dtype='>u2').astype('float')
    data_arr = (data_arr - yref) * yinc + yor

    all_data[:,i+1] = data_arr

# np.savetxt(sys.argv[2], all_data, delimiter=',', header='t,' + sys.argv[1])
np.savetxt(filename, all_data, delimiter=',', header='t,' + chan_list)

print('Starting scope')
scope.write(':RUN')

scope.close()
print('Trace recorded. Have a nice day!')