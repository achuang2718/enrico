import time
from status_monitor import StatusMonitor 
from keysight_scope import LockDetector, scope_visa_addresses, load_scopeconfig, Oscilloscope
from numpy import mean
import datetime
import threading
import sys

READING_INTERVAL = 5
ROTSPEED_VOLTAGE_THRESHOLD = 9.6
CURRENT_VOLTAGE_THRESHOLD = 0.6
READING_TIMEOUT = 60

alex_chuang_id = "W0107FQ8YSD"
yiqi_ni_id = "W0107FPUUPK"
carsten_robens_id = "W011MTT6X7F"
eric_wolf_id = "W0135CETQEM"
my_monitor = StatusMonitor(warning_interval_in_min = 0)

warning_id_list = [eric_wolf_id, alex_chuang_id, yiqi_ni_id, carsten_robens_id]
mention_string = ""
for warning_id in warning_id_list:
    mention_string = mention_string + "<@" + warning_id + ">"

def quit_function(fn_name):
    my_monitor.warn_on_slack(mention_string + '{name} took longer than {timeout} s'.format(name=fn_name, timeout=str(READING_TIMEOUT)))

def exit_after(s):
	'''
	use as decorator to exit process if 
	function takes longer than s seconds
	'''
	def outer(fn):
	    def inner(*args, **kwargs):
	        timer = threading.Timer(s, quit_function, args=[fn.__name__])
	        timer.start()
	        try:
	            result = fn(*args, **kwargs)
	        finally:
	            timer.cancel()
	        return result
	    return inner
	return outer

def get_voltage(my_scope):
	traces_df = my_scope.acquire_traces()
	mean_voltage_1 = mean(traces_df['ch1_in_VOLT'])
	mean_voltage_2 = mean(traces_df['ch2_in_VOLT'])
	
	# print("Rotspeed K intermediate (Hz): " + str(mean_voltage_1 * 1500 / 10) + " Current K Oven (A): " + str(mean_voltage_2 / 2))
	print("Current K Oven (A): " + str(mean_voltage_2 / 2))
	return (mean_voltage_1, mean_voltage_2) 

def get_scope():
	SCOPE_NAME = 'near control PC'
	def load_channel_names(SCOPE_NAME):
	    lock_channels = load_scopeconfig()['channel_names'][SCOPE_NAME]
	    lock_channels = {int(key):lock_channels[key] for key in lock_channels}
	    return lock_channels
	lock_channels = load_channel_names(SCOPE_NAME)
	scope = Oscilloscope(visa_address=scope_visa_addresses[SCOPE_NAME])
	return scope

#TODO: Add support for current going too low
@exit_after(READING_TIMEOUT)
def monitor_voltages(scope, monitor):
	rotspeed_voltage, current_voltage = get_voltage(scope)
	# if(rotspeed_voltage < ROTSPEED_VOLTAGE_THRESHOLD):
	# 	monitor.warn_on_slack(mention_string + " The turbo rotation speed voltage is: " + str(rotspeed_voltage) + "V, corresponding to a rotation speed of " + 
	# 							str(rotspeed_voltage * 150) + " Hz. This may indicate a problem!")
	if(current_voltage > CURRENT_VOLTAGE_THRESHOLD or current_voltage < 0.1):
		monitor.warn_on_slack(mention_string + " The turbo current indicator voltage is " + str(current_voltage) + "V, corresponding to a pump current of " + 
								 str(current_voltage / 2) + "A. This may indicate a problem!")

def main():
	try:
		with get_scope() as my_scope:
			print("OK I'm ready!")
			while True:
				print(datetime.datetime.today())
				print('acquiring traces')
				monitor_voltages(my_scope, my_monitor)
				time.sleep(READING_INTERVAL)

	except Exception as e:
		while True:
			my_monitor.warn_on_slack(mention_string + " The turbo logging is no longer occurring!")
			time.sleep(5)


if __name__ == "__main__":
	main()