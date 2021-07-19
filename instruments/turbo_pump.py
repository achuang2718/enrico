"""
Library to read and control remote-capable turbo pumps.
"""

import serial 
import time 



VARIAN_TWISTORR_STX = 0x02
VARIAN_TWISTORR_ETX = 0x03 
VARIAN_TWISTORR_READ = 0x30 
VARIAN_TWISTORR_WRITE = 0x31
VARIAN_TWISTORR_DEFAULT_ADDRESS = 0x80


class TurboPump:

    """Constructor.
    
    Args:
        port_name: A str containing the port name of the turbo. For "varian_twistorr", a COM port.
        pump_label: a str describing the type of turbo being controlled. Supports "varian_twistorr"
        address: The address of the pump. Defaults to default pump address: 0x80 for "varian_twistorr"
        can_control: A bool describing whether the software may write to the pump (as opposed to read-only commands). Default False
        wait_time: float, the wait time for a read after a send command. Default 0.1 sec. 
    """

    def __init__(self, port_name, pump_label, address = None, can_control = False, wait_time = 0.1):
        self.pump_label = pump_label 
        self.port_name = port_name 
        if(self.pump_label == "varian_twistorr"):
            PORT_SETTINGS = {'baudrate':9600, 'bytesize':serial.EIGHTBITS, 'parity':serial.PARITY_NONE, 'stopbits':serial.STOPBITS_ONE, 'timeout':1}
            self.port = serial.Serial(self.port_name, **PORT_SETTINGS)
        if(address == None):
            if(self.pump_label == "varian_twistorr"):
                self.address = VARIAN_TWISTORR_DEFAULT_ADDRESS
        else:
            self.address = address 
        self.can_control = can_control 
        self.wait_time = wait_time 

    
    def __enter__(self):
        return self


    def __exit__(self, exc_type, exc_value, traceback):
        if(self.pump_label == "varian_twistorr"):
            self.port.close()

    """Helper method for creating a parity checksum for the varian twistorr

    bytes_to_check: A byte array containing the bytes to be parity checked

    Returns:
    A string encoding the parity byte obtained from the check in uppercase hex.
    E.g. if the bytes checked are 0x01 and 0x03, then the output string would be '02'
    """
    def _make_twistorr_parity_checksum(bytes_to_check):
        my_int = 0
        for byte_value in bytes_to_check:
            my_int = my_int ^ byte_value
        my_hex_string = hex(my_int)
        my_trimmed_hex_string = my_hex_string[2:]
        if(len(my_trimmed_hex_string) == 1):
            my_trimmed_hex_string = "0" + my_trimmed_hex_string 
        return my_trimmed_hex_string
        

    """Helper method for making a read command to send to the varian_Twistorr turbo pump"""
    def _make_twistorr_read_command(self, window_string):
        command_byte_array = bytearray(0)
        command_byte_array.append(VARIAN_TWISTORR_STX)
        command_byte_array.append(self.address)
        window_bytes = bytes(window_string, encoding = "ASCII")
        command_byte_array.extend(window_bytes)
        command_byte_array.append(VARIAN_TWISTORR_READ)
        command_byte_array.append(VARIAN_TWISTORR_ETX)
        checksum_string = _make_twistorr_parity_checksum(command_byte_array[1:])
        checksum_bytes = bytes(checksum_string, encoding = "ASCII") 
        command_byte_array.extend(checksum_bytes) 
        return bytes(command_byte_array)


    """Helper method for making a write command to send to the varian_Twistorr turbo pump"""
    def _make_twistorr_write_command(self, window_string, data_string):
        command_byte_array = bytearray(0) 
        command_byte_array.append(VARIAN_TWISTORR_STX)
        command_byte_array.append(self.address) 
        window_bytes = bytes(window_string, encoding = "ASCII") 
        command_byte_array.extend(window_bytes) 
        command_byte_array.append(VARIAN_TWISTORR_WRITE)
        data_bytes = bytes(data_string, encoding = "ASCII") 
        command_byte_array.extend(data_bytes)
        checksum_string = _make_twistorr_parity_checksum(command_byte_array[1:]) 
        checksum_bytes = bytes(checksum_string, encoding = "ASCII") 
        command_byte_array.extend(checksum_bytes) 
        return bytes(command_byte_array) 

    """Turns on the turbo pump, i.e. starts the blades spinning.
    
    Returns True if the pump is successfully turned on, and False otherwise. Wraps pump-specific commands"""
    #TODO: Change exception handling to handle any expected exceptions from e.g. a turned-off pump
    def turn_on_pump(self):
        if(not self.can_control):
            return False
        elif(self.pump_label == "varian_twistorr"):
            return self._twistorr_turn_on_pump()

    def _twistorr_turn_on_pump(self):
        try:
            turn_on_command = self._make_twistorr_write_command('000', '1') 
            pump_response = self.send_and_get_response(turn_on_command) 
            return TurboPump._twistorr_verify_acknowledgement(pump_response) 
        except IndexError as e:
            return False 

    def turn_off_pump(self):
        if(not self.can_control):
            return False 
        elif(self.pump_label == "varian_twistorr"):
            return self._twistorr_turn_off_pump()


    def _twistorr_turn_off_pump(self):
        try:
            turn_off_command = self._make_twistorr_write_command('000', '0') 
            pump_response = self.send_and_get_response(turn_off_command) 
            return TurboPump._twistorr_verify_acknowledgement(pump_response) 
        except IndexError as e:
            return False 
            

    """Method for getting the status of the turbo pump. Wraps pump-specific methods.
    
    Returns a string indicating status. This is 'normal' for normal operation and a brief description 
    for other operation."""
    def get_status(self):
        if(self.pump_label == "varian_twistorr"):
            return self._twistorr_get_status()
    

TWISTORR_STATUS_WINDOW_STRING = '205'

    def _twistorr_get_status(self):
        try:
            get_status_command = self._make_twistorr_read_command(TWISTORR_STATUS_WINDOW_STRING) 
            pump_response = self.send_and_get_response(get_status_command) 
            status_bytes = TurboPump._twistorr_extract_response_bytes(pump_response) 
            status_byte = status_bytes[-1] 
            if(status_byte == 30):
                return 'stop'
            elif(status_byte == 31):
                return 'waiting_intlk'
            elif(status_byte == 32):
                return 'starting' 
            elif(status_byte == 33):
                return 'auto-tuning' 
            elif(status_byte == 34):
                return 'braking'
            elif(status_byte == 35):
                return 'normal'
            elif(status_byte == 36):
                return 'fail'
        except IndexError as e:
            return 'comm_error'  





    """Method for explicitly sending a command to the turbo. Wraps the pump-specific send methods.
    Args:
        command: 
            For pump type "varian_twistorr", a bytes object containing the command to be sent.
        
    Returns:
        For pump type "varian_twistorr", the return value of serial.write()
    """
    def send(self, command):
        if(self.pump_label == "varian_twistorr"):
            return_value = self._twistorr_send(command) 
        else:
            return_value = None
        time.sleep(self.wait_time)
        return return_value


    def _twistorr_send(self, command):
        return_value = self.port.write(command)
        self.port.flush()
        return return_value

    """Method for sending a command and returning the response. Wraps the pump-specific read methods.
    Args:
        command:
            For pump type "varian_twistorr", a bytes object containing the command to be sent.

    Returns:
        For pump type "varian_twistorr", a tuple (response_bytes, checksum_bytes) containing the response and a parity checksum
    """

    def send_and_get_response(self, command):
        self.send(command)
        if(self.pump_label == "varian_twistorr"):
            return self._twistorr_get_response(command) 
        else:
            return None


    def _twistorr_get_response(self):
        trimmed_response_bytes = self.port.read_until(VARIAN_TWISTORR_ETX.to_bytes(1, 'big'))
        checksum_bytes = self.port_read(2) 
        return (trimmed_response_bytes, checksum_bytes)

    #TODO: Handle checksum here
    def _twistorr_extract_response_bytes(pump_response, field_type):
        response_bytes, checksum_bytes = pump_response
        if(field_type == "logic"):
            data_bytes = response_bytes[5:6]
        elif(field_type == "numeric"):
            data_bytes = response_bytes[5:11]
        elif(field_type == "alphanumeric"):
            data_bytes = response_bytes[5:15] 
        elif(field_type == "acknowledgement"):
            data_bytes = response_bytes[5:6]
        return data_bytes

    def _twistorr_verify_acknowledgement(response_bytes):
        acknowledgement_bytes = TurboPump._twistorr_extract_response_bytes(response_bytes)
        acknowledgement_byte = acknowledgement_bytes[0]
        return (acknowledgement_byte == 0x06)

