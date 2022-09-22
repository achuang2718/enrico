# adapted from solstis_tcpip repo by rywais, https://github.com/Rywais/solstis_tcpip
import socket
from collections import Counter
import json
from warnings import warn
import numpy as np
from time import sleep, perf_counter
import datetime

# default params for socket
DEFAULT_SERVER_IP = '192.168.1.222'  # of TiSa
DEFAULT_PORT = 39933
DEFAULT_TIMEOUT = 5
DEFAULT_TRANSMISSION_ID = 1
DEFAULT_CLIENT_IP = '192.168.1.6'  # currently set for the analysis PC
print('Remember to set CONFIGURE -> NETWORK SETTINGS -> REMOTE INTERFACE in the web interface to match the client IP.')
DEBUG_MODE = False
WAVEMETER_REFRESH_TIME = 2
SOFTWARE_LOCK_TIMEOUT = 3 * 60  # seconds
# seconds. Outputs an error message if software relock is engaged twice in this interval.
MIN_RELOCK_INTERVAL = 5 * 60
LOG_FILENAME = 'tisa_softlock.csv'
ETALON_DIFF_THRESHOLD = 1  # percentage
LOCK_ENGAGE_THRESHOLD = 10e-3  # THz
GAIN_ETALON = 8 / 30e-3  # etalon percentage per THz
MAX_ETALON_STEP = 10


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
        self.last_relock_time = None
        self.etalon_setting = None

    def __enter__(self):
        pass

    def __exit__(self):
        print('Closing connection to TiSa...')
        self.sock.close()

    def _send_msg(self, operation: str, params: dict = {}, debug=DEBUG_MODE):
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

    def _verify_msg(self, msg, operation: str):
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

    def _send_and_recv_status(self, operation: str, params: dict = {}, debug=DEBUG_MODE, status_nested=True):
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
        return_dict = {param: params[param][0]
                       for param in nested_params_to_parse}
        return_dict.update({param: params[param]
                            for param in bare_params_to_parse})
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
            self.etalon_setting = setting
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

    def _get_etalon_setting(self):
        """
        Infer the etalon percentage setting from the physical voltage on the etalon. 
        """
        MAX_ETALON_VOLTAGE = 196.4
        inferred_setting = self.get_status(
        )['etalon_voltage'] / MAX_ETALON_VOLTAGE * 100
        if self.etalon_setting is None:
            self.etalon_setting = inferred_setting
        return inferred_setting  # percent

    def software_lock(self, target_frequency, wavemeter, frequency_diff_threshold=500e-6, timeout=SOFTWARE_LOCK_TIMEOUT,
                      wavemeter_refresh=WAVEMETER_REFRESH_TIME, relock_interval=MIN_RELOCK_INTERVAL,
                      log_filename=LOG_FILENAME, etalon_diff_threshold=ETALON_DIFF_THRESHOLD,
                      lock_engage_threshold=LOCK_ENGAGE_THRESHOLD,
                      gain_etalon=GAIN_ETALON, max_etalon_step=MAX_ETALON_STEP):
        """
        Uses tune_etalon to coarsely set the frequency before engaging the etalon lock. Exit conditions include (1) successful lock or
        (2) timing out after lock fails or rails. Outputs a message string for debugging.
        Parameters:
            target_frequency ~ in THz (float), typically read from wavemeter.
            wavemeter ~ object that handles reading the wavemeter.
            frequency_diff_threshold ~ in THz (float). Specifies the threshold for a successful lock.
            timeout ~ in seconds (float), after which software_lock will stop trying.
            wavemeter_refresh ~ in seconds (float) to give wavemeter time to update its reading.
            relock_interval ~ in seconds (float). Returns error if software lock is too frequently engaged.
            log_filename ~ (path or str) to .csv log file
            etalon_diff_threshold ~ (float) minimum threshold to distinguish whether etalon voltage reading and internal memory of
                etalon position differs significantly. This can occur if a human interacts with the TiSa via GUI.
            lock_engage_threshold ~ (float) maximum difference tolerated to consider engage etalon lock, otherwise etalon
            tunes freely without locking.
            gain_etalon ~ (float) etalon percentage per THz. Can be calibrated by scanning the etalon and recording the linear change in frequency.
                Make sure to set the gain sign correctly!
            max_etalon_step ~ (float) etalon percentage. Limits the change in etalon position.
        Returns:
        A tuple of
            lock_achieved ~ (bool)
            message ~ (str) Returns empty string if lock is successful and not engaging within relock interval time.
        """
        # sometimes the TiSa will jump back to its happy place by unlocking and relocking
        self.etalon_lock(False)
        sleep(wavemeter_refresh)
        self.etalon_lock(True)
        if self.last_relock_time is not None and (perf_counter() - self.last_relock_time) < relock_interval:
            debugging_message = 'Software lock has engaged twice in ' + \
                str(relock_interval / 60) + ' minutes.'
        else:
            debugging_message = ''
        current_frequency = wavemeter.GetFrequency()
        t_start = perf_counter()
        while abs(current_frequency - target_frequency) > frequency_diff_threshold:
            if current_frequency > 0:  # negative readings correspond to a wavemeter error
                inferred_setting = self._get_etalon_setting()
                if abs(self.etalon_setting - inferred_setting) > etalon_diff_threshold:
                    old_setting = self.etalon_setting
                    self.etalon_setting = inferred_setting
                    return False, """Inferred etalon setting {infer}% and etalon setting in internal memory {mem}% differs
                    by greater than 1%. Attempting to reset internal memory. Try restarting TiSa softlock if this fails.""".format(infer=str(inferred_setting),
                                                                                                                                   mem=str(old_setting))
                self.last_relock_time = perf_counter()
                self.etalon_lock(False)
                elapsed_time = perf_counter() - t_start
                print('Elapsed time: ' + str(elapsed_time))
                # etalon tuning parameter is typically increased to decrease the frequency
                etalon_sign = np.sign(current_frequency - target_frequency)
                print('current frequency (THz): ' + str(current_frequency))
                etalon_increment = min(
                    2, gain_etalon * abs(current_frequency - target_frequency))
                print('etalon increment: ')
                print(etalon_increment)
                new_etalon_setting = self.etalon_setting + etalon_sign * etalon_increment
                print('\ntrying etalon_tune: ' + str(new_etalon_setting))
                if new_etalon_setting < 0.1 or new_etalon_setting > 99.9:
                    return False, 'Etalon railed.'  # software lock fails if etalon rails
                elif elapsed_time > timeout:
                    return False, 'Software lock timed out.'
                self.tune_etalon(new_etalon_setting)
                sleep(wavemeter_refresh)
                current_frequency = wavemeter.GetFrequency()
                if abs(current_frequency - target_frequency) < lock_engage_threshold:
                    print('Frequency within {thresh}THz, engaging etalon lock.'.format(
                        thresh=str(lock_engage_threshold)))
                    self.etalon_lock(True)
                with open(log_filename, 'a') as f:
                    f.write('{timestamp}, {etalon}, {freq}\n'.format(timestamp=str(datetime.datetime.now()),
                                                                     etalon=str(new_etalon_setting), freq=str(current_frequency)))
            else:
                return False, 'Invalid wavemeter reading. Is the wavemeter underexposed?'

        return True, debugging_message

    def characterize_mode_hops(self, wlm, etalon_range=0.05, num_points=10, refresh_time=WAVEMETER_REFRESH_TIME):
        if self.etalon_setting is None:
            initial_setting = float(input('Enter the current etalon tune setting (%): '))
            self.etalon_setting = initial_setting
        else:
            initial_setting = self.etalon_setting
        counter = 0
        increment_sign = 1
        etalon_settings, freqs_before_etalon_lock, freqs_after_etalon_lock = [], [], []
        while counter < num_points:
            counter += 1
            etalon_settings.append(
                self.etalon_setting + increment_sign * 0.01)
            self.tune_etalon(etalon_settings[-1])
            sleep(refresh_time)
            freqs_before_etalon_lock.append(wlm.GetFrequency())
            self.etalon_lock(True)
            sleep(refresh_time)
            freqs_after_etalon_lock.append(wlm.GetFrequency())
            print(abs(etalon_settings[-1] - initial_setting), increment_sign)
            if abs(etalon_settings[-1] - initial_setting) > etalon_range:
                increment_sign *= -1

            print(
                etalon_settings[-1], freqs_before_etalon_lock[-1], freqs_after_etalon_lock[-1])
            
            with open('tisa_characterization.log', 'a') as f:
                f.write('{timestamp}, {etalon}, {freq_before}, {freq_after}\n'.format(timestamp=str(datetime.datetime.now()),
                                                                                      etalon=str(etalon_settings[-1]), freq_before=str(freqs_before_etalon_lock[-1]),
            
                                                                                      freq_after=freqs_after_etalon_lock[-1]))
            self.etalon_lock(False)
            sleep(refresh_time)

        return etalon_settings, freqs_before_etalon_lock, freqs_after_etalon_lock

# THE SECTION BELOW CURRENTLY DOES NOT TUNE THE TARGET LAMBDA
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


def main():
    from wlm import WavelengthMeter
    my_wlm = WavelengthMeter()
    IDEAL_FREQ = 390.983
    try:
        my_tisa = Solstis()
        etalon_settings, freqs_before_etalon_lock, freqs_after_etalon_lock = my_tisa.characterize_mode_hops(
            my_wlm, etalon_range=1, num_points=2000, refresh_time=1)
    finally:
        my_tisa.__exit__()


if __name__ == "__main__":
    main()
