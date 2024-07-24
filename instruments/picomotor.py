"""
Library to control the picomotor driver.
"""

import serial
import time
import datetime
from collections import OrderedDict
from random import randint
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.dates as mdates
import warnings
import matplotlib.cbook
warnings.filterwarnings("ignore", category=matplotlib.cbook.mplDeprecation)


def get_key(my_dict, val):
    for key, value in my_dict.items():
        if val == value:
            return key


class MSerial:
    axis_names = dict(x=0, y=1)
    unit = dict(x=1, y=1)

    def __init__(self, port, echo=True, max_retry=2, wait=0.1, sendwidget=None, recvwidget=None, **serial_kws):
        kws = dict(baudrate=19200, bytesize=serial.EIGHTBITS,
                   parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE,
                   timeout=0, xonxoff=True, rtscts=False, dsrdtr=False)
        kws.update(serial_kws)
        self.serial = serial.Serial(port, **kws)
        self.echo = echo
        self.wait = wait
        self.sendwidget = sendwidget
        self.recvwidget = recvwidget
        self.history = {}
        for idx in range(1, 4):
            self.history[str(idx)] = {str(idx): OrderedDict()
                                      for idx in range(0, 3)}
        self.MAX_LENGTH = 1e3
        self.aliases = {'DShape horiz': (1, 0),
                        'CODT horiz': (1, 1), 'CODT vert': (1, 2),
                        'DShape vert': (2, 0),
                        'Downleg horiz': (2, 1), 'Downleg vert': (2, 2),
                        'PODT horiz': (3, 0), 'PODT vert': (3, 1),
                        'unused': (3, 2),
                        }
        print('Nine available channels should appear below.')
        self.sendrecv('INI')
        self.sendrecv('ACC')

    def send(self, cmd):
        """Send a command to the picomotor driver."""
        line = cmd + '\r\n'
        retval = self.serial.write(bytes(line, encoding='ascii'))
        self.serial.flush()
        if self.echo:
            self.log(cmd, widget=self.sendwidget)
        return retval

    def readlines(self):
        """Read response from picomotor driver."""
        return ''.join([l.decode('ASCII') for l in self.serial.readlines()])

    def log(self, msg, widget=None):
        if widget is None:
            print(msg, flush=True)
        else:
            widget.value = msg

    def sendrecv(self, cmd):
        """Send a command and (optionally) printing the picomotor driver's response."""
        res = self.send(cmd)
        if self.echo:
            time.sleep(self.wait)
            ret_str = self.readlines()
            self.log(ret_str, widget=self.recvwidget)
        return res

    def update_motor_history(self, driver_idx, motor_idx, step_size):
        # TODO

        driver_key = str(driver_idx)
        motor_key = str(motor_idx)
        # time_now = datetime.datetime.today().strftime('%Y-%m-%d %H:%M:%S')
        time_now = datetime.datetime.today()
        self.history[driver_key][motor_key][time_now] = step_size
        if len(self.history[driver_key][motor_key]) > self.MAX_LENGTH:
            self.history[driver_key][motor_key].popitem(last=False)
        print(time_now)

    def move(self, alias=None, step_size=None, MAX_STEP_SIZE=50, WAIT_TIME_BETWEEN_MAX_STEPS=0.5):
        def signum(x):
            return (x > 0) - (x < 0)

        if not isinstance(step_size, int):
            return ValueError('step_size must be an integer.')
        sign = signum(step_size)

        if alias is None:
            print('Named driver ports include {ports}'.format(
                ports=str(self.aliases.keys())))
            alias = input('Enter name: ')
        if step_size is None:
            step_size = int(input('Enter step size: '))

        driver_idx, motor_idx = self.aliases[alias]

        print('{alias} (motor {motor} on driver a{driver}) moving {step} steps'.format(motor=str(motor_idx),
                                                                                       driver=str(
                                                                                           driver_idx),
                                                                                       step=str(
                                                                                           step_size),
                                                                                       alias=alias))
        self.update_motor_history(driver_idx, motor_idx, step_size)

        # step in +/- MAX_STEP_SIZE increments until |remaining step_size| <= 50.
        while step_size * sign > MAX_STEP_SIZE:
            active_motor_cmd = 'chl a{driver}={motor}'.format(
                driver=str(driver_idx), motor=str(motor_idx))
            self.sendrecv(active_motor_cmd)
            move_cmd = 'rel {driver} {step} g'.format(
                driver=str(driver_idx), step=str(sign * MAX_STEP_SIZE))
            self.sendrecv(move_cmd)
            step_size += -MAX_STEP_SIZE * sign
            print(str(step_size) + ' remaining')
            time.sleep(WAIT_TIME_BETWEEN_MAX_STEPS)
        if step_size * sign > 0:
            active_motor_cmd = 'chl a{driver}={motor}'.format(
                driver=str(driver_idx), motor=str(motor_idx))
            self.sendrecv(active_motor_cmd)
            move_cmd = 'rel {driver} {step} g'.format(
                driver=str(driver_idx), step=str(step_size))
            self.sendrecv(move_cmd)

    def status_msg(self):
        """Return the driver status byte as an integer (see manual pag. 185)."""
        self.send('STA')
        time.sleep(self.wait)
        ret_str = self.readlines()
        if self.echo:
            self.log(repr(ret_str), widget=self.recvwidget)
        return ret_str

    def status(self):
        ret_str = self.status_msg()
        i = ret_str.find('A1=')
        if i >= 0:
            status = int(ret_str[i + 5:i + 7], 16)
        else:
            raise IOError("Received: '%s'" % ret_str)
        return status

    def is_moving(self):
        """Return True if motor is moving, else False."""
        status = self.status()
        return status & 0x01

    def plot_positions(self, xaxis='move_idx'):
        plt.style.use('seaborn')
        i = 1
        for driver_key in self.history:
            for motor_key in self.history[driver_key]:
                plt.subplot(len(self.history), 2, i)
                x_data = list(self.history[driver_key][motor_key].keys())
                y_data = np.cumsum(
                    list(self.history[driver_key][motor_key].values()))
                label = get_key(
                    self.aliases, (int(driver_key), int(motor_key)))
                plt.plot(x_data, y_data, marker='o',
                         linestyle='dashed', label=label)

                plt.legend(loc='best')
                plt.xlabel('time (TODO: formatting)')
                plt.ylabel('position')
            i += 2
        i = 2
        for driver_key in self.history:
            for motor_key in self.history[driver_key]:
                plt.subplot(len(self.history), 2, i)
                x_data = list(self.history[driver_key][motor_key].keys())
                y_data = list(self.history[driver_key][motor_key].values())
                label = get_key(
                    self.aliases, (int(driver_key), int(motor_key)))
                plt.plot(x_data, y_data, marker='o',
                         linestyle='dotted', label=label)
                plt.legend(loc='best')
                plt.xlabel('time (TODO: formatting)')
                plt.ylabel('step size')
            i += 2

        plt.tight_layout()
        plt.show()

    def pickle(self):
        # save histories in .pkl file
        pass


# picomotor_COMPORT = 'COM4'
# picomotor = MSerial(picomotor_COMPORT)
# print('\n INFO: picomotor has methods picomotor.move(alias=ALIAS_HERE, step_size=STEP_SIZE_HERE), picomotor.plot_positions(). \n move() called without args will require further manual input \n \n Try something like picomotor.move(alias=\'flex\',step_size=5) or picomotor.move() \n')


from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QPlainTextEdit,
                             QHBoxLayout, QVBoxLayout, QWidget, QInputDialog, QLineEdit, QMessageBox,
                             QRadioButton, QButtonGroup, QCheckBox, QLabel)
from PyQt5.QtCore import QProcess
from PyQt5.QtGui import QFont, QIntValidator
import sys

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

class MplCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        plt.style.use('seaborn')
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.ax1 = fig.add_subplot(311)
        self.ax2 = fig.add_subplot(312)
        self.ax3 = fig.add_subplot(313)
        super(MplCanvas, self).__init__(fig)

class PicomotorGUI(QMainWindow):
    def __init__(self, PICOMOTOR_COMPORT='COM7'):
        super().__init__()

################DELETE AFTER GUI TESTING#####################################
        # aliases = {'DShape horiz': (1, 0),
        #            'CODT horiz': (1, 1), 'CODT vert': (1, 2),
        #            'DShape vert': (2, 0),
        #            'Downleg horiz': (2, 1), 'Downleg vert': (2, 2),
        #            'PODT horiz': (3, 0), 'PODT vert': (3, 1),
        #            'unused': (3, 2),
        #            }.keys()
#############################################################################

        self.picomotor = MSerial(PICOMOTOR_COMPORT)
        aliases = self.picomotor.aliases.keys()

        self.setWindowTitle('Picomotor')
        layout = QHBoxLayout()

        # create motor buttons
        self.selectmotor_buttons = QButtonGroup()
        motorVBox = QVBoxLayout()
        for alias in aliases:
            button_name = alias.replace(' ', '_') + 'radiobutton'
            setattr(self, button_name, QRadioButton(alias))
            button = getattr(self, button_name)
            button.toggled.connect(
                self.set_active_motor)
            self.selectmotor_buttons.addButton(button)
            motorVBox.addWidget(button)

        # create step size input widget
        self.step_size_input = QLineEdit()
        self.step_size_input.setValidator(QIntValidator(-2000, 2000))
        self.step_size_input.returnPressed.connect(self.send_move_cmd)
        motorVBox.addWidget(QLabel('Enter step size:'))
        motorVBox.addWidget(self.step_size_input)
        self.move_button = QPushButton("move")
        self.move_button.pressed.connect(self.send_move_cmd)
        motorVBox.addWidget(self.move_button)
        self.clear_button = QPushButton("clear history")
        self.clear_button.pressed.connect(self.clear_history)
        motorVBox.addWidget(self.clear_button)
        w = QWidget()
        layout.addLayout(motorVBox)

        self.canvas = MplCanvas(self, width=5, height=4, dpi=100)
        layout.addWidget(self.canvas)
        # w.setLayout(motorVBox)
        w.setLayout(layout)
        self.setCentralWidget(w)

    def send_move_cmd(self):
        step_size = int(self.step_size_input.text())
        self.picomotor.move(alias=self.active_motor, step_size=step_size)
        print('sending self.picomotor.move(alias={active_motor}, step_size={step_size}).'.format(
            active_motor=self.active_motor, step_size=str(step_size)))
        #plot picomotor histories
        i = 0
        history = self.picomotor.history
        axes = [self.canvas.ax1, self.canvas.ax2, self.canvas.ax3]
        for driver_key in history:
            ax = axes[i]
            ax.cla()
            i += 1
            for motor_key in history[driver_key]:
                x_data = list(history[driver_key][motor_key].keys())
                y_data = np.cumsum(
                    list(history[driver_key][motor_key].values()))
                label = get_key(
                    self.picomotor.aliases, (int(driver_key), int(motor_key)))
                # label = (int(driver_key), int(motor_key))
                ax.plot(x_data, y_data, marker='o',
                         linestyle='dashed', label=label)
                ax.legend(loc='best')
                ax.set_xlabel('time (TODO: formatting)')
                ax.set_ylabel('position')
        self.canvas.draw()

    def set_active_motor(self):
        radioBtn = self.sender()
        if radioBtn.isChecked():
            motor_alias = radioBtn.text()
            self.active_motor = motor_alias
            print(self.active_motor + ' selected.')

    def clear_history(self):
        axes = [self.canvas.ax1, self.canvas.ax2, self.canvas.ax3]
        for ax in axes:
            ax.cla()
        self.canvas.draw()
        self.picomotor.history = {}
        for idx in range(1, 4):
            self.picomotor.history[str(idx)] = {str(idx): OrderedDict()
                                      for idx in range(0, 3)}


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    w = PicomotorGUI()
    w.show()

    app.exec_()
