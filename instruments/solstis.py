# adapted from solstis_tcpip repo by rywais, https://github.com/Rywais/solstis_tcpip
import socket
from collections import Counter
import json
from warnings import warn

# default params for socket
DEFAULT_SERVER_IP = '192.168.1.222'  # of TiSa
DEFAULT_PORT = 39933
DEFAULT_TIMEOUT = 5
DEFAULT_TRANSMISSION_ID = 1
DEFAULT_CLIENT_IP = '192.168.1.4' #currently set for the analysis PC
print('Remember to set CONFIGURE -> NETWORK SETTINGS -> REMOTE INTERFACE in the web interface to match the client IP.')
DEBUG_MODE = False


class SolstisError(Exception):
    '''Exception raised when the Solstis response indicates an error
    Attributes:
      message ~ explanation of the error
    '''

    def __init__(self, message):
        self.message = message


class Solstis():
    '''
    Read out and control M Squared TiSa over TCP/IP.
    '''

    def __init__(self, server_address=DEFAULT_SERVER_IP, port=DEFAULT_PORT, timeout=DEFAULT_TIMEOUT,
                 transmission_id=DEFAULT_TRANSMISSION_ID, client_address=DEFAULT_CLIENT_IP,
                 debug=True):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((server_address, port))
        self.sock.settimeout(timeout)
        self.transmission_id = transmission_id
        self.client_address = client_address
        self._start_link()

    def __enter__(self):
        pass

    def __exit__(self):
        print('Closing connection to TiSa...')
        self.sock.close()

    def _send_msg(self, operation : str, params : dict={}, debug=DEBUG_MODE):
        '''
        Function to carry out the most basic communication send function
        transmission_id ~ Arbitrary(?) integer
        op ~ String containing operating command
        params ~ dict containing Solstis Key/Value pairs as necessary
        '''
        message = {'transmission_id': [self.transmission_id], 'op': operation}
        if len(params) > 0:
            message['parameters'] = params
        command = {'message': message}
        send_msg = json.dumps(command).encode('utf8')
        if debug == True:
            print(send_msg)
        self.sock.sendall(send_msg)

    def _recv_msg(self, timeout=10., debug=DEBUG_MODE):
        '''
        Receives stream until a full json payload is completed.
        Returns:
            A dictionary parsed from the json payload.
        '''
        s = self.sock
        data = s.recv(1024).decode('utf8')

        # Check that the message starts with a '{'
        if data[0] != '{':
            print('received: ' + data)
            raise SolstisError('Received data from TCP/IP is invalid.')

        # parse received data as json
        while True:
            my_counter = Counter(data)
            # reception completed after receiving final right-brace
            if my_counter['{'] == my_counter['}']:
                break
            else:
                data += s.recv(1024).decode('utf8')
        if debug:
            print(data)
        return json.loads(data)

    def _verify_msg(self, msg, operation : str):
        '''
        Verifies that the received message matches the sent request, at a syntactical level.
        Messages still need to be parsed on a case-by-case basis.
        '''
        msg_ID = msg['message']['transmission_id'][0]
        msg_OP = msg['message']['op']
        # if msg_ID != self.transmission_id:
        #     err_msg = 'Message with ID' + str(msg_ID) + ' did not match expected ID of: ' +\
        #         str(self.transmission_id)
        #     raise SolstisError(err_msg)
        if msg_OP == 'parse_fail':
            err_msg = 'Message with ID ' + str(msg_ID) + ' failed to parse.'
            err_msg += '\n\n' + str(msg)
            raise SolstisError(err_msg)
        if msg_OP != operation:
            msg = 'Message with ID' + str(msg_ID) + 'with operation command of '' + msg_OP +\
                  '' did not match expected operation command of: ' + operation
            raise SolstisError(msg)

    def _send_and_recv_status(self, operation : str, params : dict={}, debug=DEBUG_MODE, status_nested=True):
        '''
        Sends and receives status of operation.
        Returns:
            msg ~ json payload parsed as dict
            status ~ either a string (e.g. 'ok') or status code int (e.g. 1), depending on the operation
        '''
        self._send_msg(operation=operation, params=params, debug=debug)
        msg = self._recv_msg()
        self._verify_msg(msg, operation=operation + '_reply')
        if status_nested:
            status = msg['message']['parameters']['status'][0]
        else:
            status = msg['message']['parameters']['status']
        return msg, status

    def _start_link(self):
        _, status = self._send_and_recv_status(operation='start_link', params={
            'ip_address': self.client_address}, status_nested=False)
        if status == 'ok':
            return
        elif status == 'failed':
            raise SolstisError('Link could not be formed')
        else:
            raise SolstisError(
                'Unknown error: Could not determine link status')

    def get_status(self):
        '''Retrieves the system status information available to the user

        Parameters:
          sock ~ Socket object to use
          transmission_id ~ (int) arbitrary integer to use for communications
        Returns:
          A dictionary containing the following key/value pairs:
            'status' ~ 0 on a succesful call, and 1 otherwise
            'wavelength' ~ The current wavelength in nm
            'temperature' ~ Current temperature in degrees Celcius
            'temperature_status' ~ 'on' or 'off'
            'etalon_lock' ~ 'on','off','debug','error','search' or 'low'. See Manual.
            'etalon_voltage' ~ Reading in Volts
            'cavity_lock' ~ 'on','off','debug','error','search' or 'low'
            'resonator_voltage' ~ Reading in Volts
            'ecd_lock' ~ 'not_fitted','on','off','debug','error','search' or 'low'
            'ecd_voltage' ~ Reading in Volts
            'output_monitor' ~ Reading in Volts
            'etalon_pd_dc' ~ Reading in Volts
            'dither' ~ 'on' or 'off'
        Raises:
          SolstisError on operation failure
        '''

        msg, status = self._send_and_recv_status(
            operation='get_status', status_nested=True)
        if status == 1:
            raise SolstisError('get_status failed: reason unknown')
        params = msg['message']['parameters']
        nested_params_to_parse = ['wavelength', 'temperature', 'etalon_voltage',
                                  'resonator_voltage', 'output_monitor', 'etalon_pd_dc', 'status']
        bare_params_to_parse = ['temperature_status',
                                'etalon_lock', 'cavity_lock', 'ecd_lock', 'dither']
        return_dict = {param: params[param][0] for param in nested_params_to_parse}
        return_dict.update({param: params[param] for param in bare_params_to_parse})
        if params['ecd_voltage'] == 'not_fitted':
            return_dict['ecd_voltage'] = -float('inf')
        else:
            return_dict['ecd_voltage'] = params['ecd_voltage'][0]
        warn('BUG: etalon_lock status does not reflect the physical state of the etalon lock!')
        return return_dict

    def tune_etalon(self, setting):
        '''Tunes the etalon to user-defined value

        Parameters:
          setting ~ (float) Percentage (0-100) of etalon range to go to
        Returns:
          Nothing on success
        Raises:
          SolstisError on failure to execute
        '''

        _, status = self._send_and_recv_status('tune_etalon', {'setting': [setting]},
                                               status_nested=True)
        if status == 0:
            return
        elif status == 1:
            raise SolstisError('Etalon Tuning value is out of range.')
        else:
            raise SolstisError('tune_etalon Failed; Reason Unknown')

    def etalon_lock(self, lock):
        '''Either locks or unlocks the etalon

        Parameters:
          sock ~ Socket object to use for communications
          lock ~ (Boolean) True to lock the etalon, False to unlock it
          transmission_id ~ (int) arbitrary integer for use in communications
        Returns:
          Nothing on success
        Raises:
          SolstisError on failure
        '''
        lock_command_dict = {True: 'on', False: 'off'}

        _, status = self._send_and_recv_status(
            'etalon_lock', {'operation': lock_command_dict[lock]})
        if status == 0:
            return
        else:
            raise SolstisError('etalon_lock Failed; Reason Unknown')

#THE SECTION BELOW CURRENTLY DOES NOT TUNE THE TARGET LAMBDA
##################################################################################
    # def set_wave_m(self, wavelength):
    #     '''Sets the wavelength based on wavelength table

    #     Parameters:
    #       sock ~ socket object to use
    #       wavelength ~ (float) wavelength set point
    #       transmission_id ~ (int) Arbitrary integer for communications
    #     Returns:
    #       Nothing
    #     '''

    #     _, status = self._send_and_recv_status(
    #         'set_wave_m', {'wavelength': [wavelength]}, status_nested=True)
    #     if status == 0:
    #         pass
    #     elif status == 1:
    #         raise SolstisError(
    #             'move_wave_t: Failed, is your wavemeter configured?')
    #     else:
    #         raise SolstisError('Wavelength out of range.')
##################################################################################
