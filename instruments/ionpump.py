"""
Library to read and control the ion pump through RS-232. 

Use a ***NULL MODEM*** cable to connect to your PC.
"""

import serial
import os
import time
import datetime

MPC_DEFAULT_ADDRESS = 5
SPC_DEFAULT_ADDRESS = 1


class IonPump:

    """Constructor.

    Args:
        pump_label: str, the label describing the type of pump. Supports "spc" and "mpc".
        COM_PORT: str, the string describing the COM port of the pump serial connection, e.g. 'COM7'
        address: int, the address of the pump. Default is 1 for spc, 5 for mpc
        echo: bool, whether to echo the response after a send command
        wait_time: float, the wait time for a read after a send command
        sendwidget: Widget; ignore unless making a gui
        recvwidget: Widget; ignore unless making a gui
    """

    def __init__(self, pump_label, COM_PORT, address=None, echo=True, wait_time=0.1, sendwidget=None, recvwidget=None):
        # Default port settings for ion pumps
        PORT_SETTINGS = {'baudrate': 9600, 'bytesize': serial.EIGHTBITS,
                         'parity': serial.PARITY_NONE, 'stopbits': serial.STOPBITS_ONE, 'timeout': 1}
        self.serial_port = serial.Serial(COM_PORT, **PORT_SETTINGS)
        self.pump_label = pump_label
        self.echo = echo
        self.wait_time = wait_time
        self.sendwidget = sendwidget
        self.recvwidget = recvwidget

        if(address is None):
            if(pump_label == "mpc"):
                self.address = MPC_DEFAULT_ADDRESS
            elif(pump_label == "spc"):
                self.address = SPC_DEFAULT_ADDRESS
        else:
            self.address = address

    """
    Sends an arbitrary command to the ion pump

    Args: 
        command: str, the command to be sent to the ion pump
        add_checksum_and_end: Convenience. If True, the command string has a checksum and carriage return character 
        appended, following the initial tilde convention
    
    Returns:
        the return value of serial.write() 
    """

    def send(self, command, add_checksum_and_end=False):
        if(add_checksum_and_end):
            to_be_checked_string = command[1:]
            checksum_string = get_checksum_string(to_be_checked_string)
            command = command + checksum_string + "\r"
        return_value = self.serial_port.write(bytes(command, encoding="ASCII"))
        self.serial_port.flush()
        if(self.echo):
            self.log(command, widget=self.sendwidget)
        time.sleep(self.wait_time)
        return return_value

    """Convenience method which turns on the ion pump"""
    # def turn_on(self):
    #     ON_COMMAND_STRING = ""
    #     address_string = hex(self.address)[2:]
    #     address_string = address_string.upper()
    #     if(self.address < 16):
    #         address_string = "0" + address_string

    """Convenience method which measures the ion pump current, pressure, and voltage"""

    def measure_all(self, supply_index=1):
        current_value = self.measure_current(supply_index=supply_index)
        pressure_value = self.measure_pressure(supply_index=supply_index)
        voltage_value = self.measure_voltage(supply_index=supply_index)
        return (current_value, pressure_value, voltage_value)

    def measure_current(self, supply_index=1):
        if(self.pump_label == "spc"):
            data_field = ''
        elif(self.pump_label == "mpc"):
            data_field = str(supply_index) + ' '
        address_string = self.get_address_string()
        CURRENT_MEASURE_CODE = '0A'
        current_measure_command_initial = ' ' + address_string + \
            ' ' + CURRENT_MEASURE_CODE + " " + data_field
        current_measure_command_checksum = self.get_checksum_string(
            current_measure_command_initial)
        current_measure_command = '~' + current_measure_command_initial + \
            current_measure_command_checksum + "\r"
        current_bytes_list = self.send_and_get_response(
            current_measure_command)
        current_value = self.parse_current_bytes(current_bytes_list)
        return current_value

    def measure_pressure(self, supply_index=1):
        if(self.pump_label == "spc"):
            data_field = ''
        elif(self.pump_label == "mpc"):
            data_field = str(supply_index) + ' '
        address_string = self.get_address_string()
        PRESSURE_MEASURE_CODE = '0B'
        pressure_measure_command_initial = ' ' + address_string + \
            ' ' + PRESSURE_MEASURE_CODE + " " + data_field
        pressure_measure_command_checksum = self.get_checksum_string(
            pressure_measure_command_initial)
        pressure_measure_command = '~' + pressure_measure_command_initial + \
            pressure_measure_command_checksum + "\r"
        pressure_bytes_list = self.send_and_get_response(
            pressure_measure_command)
        pressure_value = self.parse_pressure_bytes(pressure_bytes_list)
        return pressure_value

    def measure_voltage(self, supply_index=1):
        if(self.pump_label == "spc"):
            data_field = ''
        elif(self.pump_label == "mpc"):
            data_field = str(supply_index) + ' '
        address_string = self.get_address_string()
        VOLTAGE_MEASURE_CODE = '0C'
        voltage_measure_command_initial = ' ' + address_string + \
            ' ' + VOLTAGE_MEASURE_CODE + " " + data_field
        voltage_measure_command_checksum = self.get_checksum_string(
            voltage_measure_command_initial)
        voltage_measure_command = '~' + voltage_measure_command_initial + \
            voltage_measure_command_checksum + "\r"
        voltage_bytes_list = self.send_and_get_response(
            voltage_measure_command)
        voltage_value = self.parse_voltage_bytes(voltage_bytes_list)
        return voltage_value

    @staticmethod
    def parse_current_bytes(current_bytes_list):
        current_string = current_bytes_list[0].decode("ASCII")
        status_code = current_string[3:5]
        if(status_code == "OK"):
            current_value_string = current_string[9:15]
            current_value = float(current_value_string)
            return current_value
        else:
            return -1

    @staticmethod
    def parse_pressure_bytes(pressure_bytes_list):
        pressure_string = pressure_bytes_list[0].decode("ASCII")
        status_code = pressure_string[3:5]
        if(status_code == "OK"):
            pressure_value_string = pressure_string[9:15]
            pressure_value = float(pressure_value_string)
            return pressure_value
        else:
            return -1

    @staticmethod
    def parse_voltage_bytes(voltage_bytes_list):
        voltage_string = voltage_bytes_list[0].decode("ASCII")
        status_code = voltage_string[3:5]
        if(status_code == "OK"):
            voltage_value_string = voltage_string[9:13]
            voltage_value = int(voltage_value_string)
            return voltage_value
        else:
            return -1

    def get_address_string(self):
        address_string = hex(self.address)[2:]
        address_string = address_string.upper()
        if(self.address < 16):
            address_string = "0" + address_string
        return address_string

    @staticmethod
    def get_checksum_string(checked_string):
        checksum_val = 0
        for byte in checked_string.encode("ASCII"):
            checksum_val += int(byte)
        checksum_val = checksum_val % 256
        checksum_string = hex(checksum_val)[2:]
        checksum_string = checksum_string.upper()
        if(checksum_val < 16):
            checksum_string = "0" + checksum_string
        return checksum_string

    def send_and_get_response(self, command, add_checksum_and_end=False):
        self.send(command, add_checksum_and_end=add_checksum_and_end)
        return self.serial_port.readlines()
