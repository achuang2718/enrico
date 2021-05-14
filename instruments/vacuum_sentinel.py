from vacuum_monitor import VacuumMonitor
import time

#Configure sampling rate, etc.
DELAY_TIME = 5
SAMPLES_PER_LOG = 12
ERROR_PATIENCE = 3
THRESHOLD_PATIENCE = 3
SLACK_ERROR_REUPDATE_TIME_SECS = 1800
SLACK_THRESHOLD_REUPDATE_TIME_SECS = 600

PRINT_VALUES = True

#Configure addresses for vacuum monitors
NA_OVEN_ADDRESS = "COM9"
K_INTERMEDIATE_ADDRESS = "COM10"
MAIN_AND_NA_INTERMEDIATE_ADDRESS = "COM11"
K_OVEN_ADDRESS = "COM12"

NA_OVEN_THRESHOLD_PRESSURE = 1e-7
K_OVEN_THRESHOLD_PRESSURE = 1e-5
MAIN_THRESHOLD_PRESSURE = 1e-10
NA_INTERMEDIATE_THRESHOLD_PRESSURE = 1e-9
K_INTERMEDIATE_THRESHOLD_PRESSURE = 2e-8

#Configure settings for who to warn in a vacuum emergency
#new_ids after migrating to MIT enterprise
alex_chuang_id = "W0107FQ8YSD"
yiqi_ni_id = "W0107FPUUPK"
carsten_robens_id = "W011MTT6X7F"
eric_wolf_id = "W0135CETQEM"

warning_id_list = [eric_wolf_id, alex_chuang_id, yiqi_ni_id, carsten_robens_id]
mention_string = ""
for warning_id in warning_id_list:
    mention_string = mention_string + "<@" + warning_id + ">"

def main():
	my_monitor = VacuumMonitor([("NA_OVEN_PUMP", NA_OVEN_ADDRESS, "pump_spc", ['pressure'], {'pressure':NA_OVEN_THRESHOLD_PRESSURE}, {}),
								("K_OVEN_PUMP", K_OVEN_ADDRESS, "pump_spc", ['pressure'], {'pressure':K_OVEN_THRESHOLD_PRESSURE}, {}),
								("K_INTERMEDIATE_PUMP", K_INTERMEDIATE_ADDRESS, "pump_spce", ['pressure'], {'pressure':K_INTERMEDIATE_THRESHOLD_PRESSURE}, {}),
								("MAIN(1)_AND_NA_INTERMEDIATE(2)_Pump", MAIN_AND_NA_INTERMEDIATE_ADDRESS, "pump_mpc", ['pressure1', 'pressure2'], {'pressure1': MAIN_THRESHOLD_PRESSURE, 'pressure2':NA_INTERMEDIATE_THRESHOLD_PRESSURE}, {})],
								local_log_filename = "Vacuum_Log.csv")
	old_time = time.time()
	counter = 0
	error_count = 0
	threshold_count = 0
	local_logger_bool = True
	threshold_fault = False
	error_fault = False
	error_old_time = 0.0
	threshold_old_time = 0.0
	try:
		while(True):
			current_time = time.time()
			if(current_time - old_time > DELAY_TIME or current_time - old_time < 0):
				old_time = current_time
				local_logger_bool = (counter % SAMPLES_PER_LOG == 0)
				counter += 1
				readings_dict, errors_list, thresholds_list = my_monitor.monitor_once(log_local = local_logger_bool)
				if(PRINT_VALUES):
					print(readings_dict)
				if(len(errors_list) != 0):
					error_count += 1
					errors_string = ""
					for error_name in errors_list:
						errors_string = errors_string + error_name + ", "
					if(error_count >= ERROR_PATIENCE and not error_fault):
						error_fault = True
						error_warning_string = mention_string + "VACUUM_ERROR: The vacuum monitor is unable to read from the following instruments: " + errors_string
						my_monitor.warn_on_slack(error_warning_string)
						error_old_time = time.time()
					elif(error_fault):
						error_current_time = time.time()
						if(error_current_time - error_old_time > SLACK_ERROR_REUPDATE_TIME_SECS):
							error_old_time = error_current_time
							error_update_string = "VACUUM_ERROR_UPDATE: The reading error persists. Vacuum monitor is unable to read from the following instruments: " + errors_string
							my_monitor.warn_on_slack(error_update_string)
				elif(error_count > 0):
					error_count -= 1
					if(error_count < ERROR_PATIENCE and error_fault):
						error_fault = False
						my_monitor.warn_on_slack("VACUUM_ERROR_RESOLVED: The outstanding reading error has been resolved.")
				if(len(thresholds_list) != 0):
					threshold_count += 1
					thresholds_string = ""
					for threshold_tuple in thresholds_list:
						reading_key, value, threshold = threshold_tuple
						thresholds_string = thresholds_string + reading_key + ", value = " + str(value) + ", threshold = " + str(threshold) + "; "
					if(threshold_count >= THRESHOLD_PATIENCE and not threshold_fault):
						threshold_fault = True
						threshold_warning_string = mention_string + "VACUUM_THRESHOLD_EXCEEDED: The following vacuum readings are above threshold: " + thresholds_string
						my_monitor.warn_on_slack(threshold_warning_string)
						threshold_old_time = time.time()
					elif(threshold_fault):
						threshold_current_time = time.time()
						if(threshold_current_time - threshold_old_time > SLACK_THRESHOLD_REUPDATE_TIME_SECS):
							threshold_old_time = threshold_current_time
							threshold_update_string = "VACUUM_THRESHOLD_UPDATE: The following values are still above threshold: " + thresholds_string
							my_monitor.warn_on_slack(threshold_update_string)
				elif(threshold_count > 0):
					threshold_count -= 1
					if(threshold_count < THRESHOLD_PATIENCE and threshold_fault):
						threshold_fault = False
						my_monitor.warn_on_slack("VACUUM_THRESHOLD_RESOLVED: The outstanding threshold warning has been resolved. All vacuum values below threshold.")
	except Exception as e:
		my_monitor.warn_on_slack(mention_string + " VACUUM_MONITOR_SHUTDOWN: An exception has crashed the vacuum monitoring.")
		raise e
if __name__ == "__main__":
	main()

