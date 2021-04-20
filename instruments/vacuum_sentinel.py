from vacuum_monitor import VacuumMonitor
import time

#Configure sampling rate, etc. 
DELAY_TIME = 5
SAMPLES_PER_LOG = 12
ERROR_PATIENCE = 3
THRESHOLD_PATIENCE = 3

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
K_INTERMEDIATE_THRESHOLD_PRESSURE = 1e-8

#Configure settings for who to warn in a vacuum emergency
alex_chuang_id = "UCL98903C"
yiqi_ni_id = "UATPBPT38"
carsten_robens_id = "UATPCKZ2A"
eric_wolf_id = "U01320WR8KE"

warning_id_list = [alex_chuang_id, yiqi_ni_id, carsten_robens_id, eric_wolf_id] 
mention_string = ""
for warning_id in warning_id_list:
    mention_string = mention_string + "<@" + warning_id + ">"

def main():
	my_monitor = VacuumMonitor([("NA_OVEN_PUMP", NA_OVEN_ADDRESS, "pump_spc", ['pressure'], {'pressure':NA_OVEN_THRESHOLD_PRESSURE}, {}),
								("K_OVEN_PUMP", K_OVEN_ADDRESS, "pump_spc", ['pressure'], {'pressure':K_OVEN_THRESHOLD_PRESSURE}, {}),
								("K_INTERMEDIATE_PUMP", K_INTERMEDIATE_ADDRESS, "pump_spc", ['pressure'], {'pressure':K_INTERMEDIATE_THRESHOLD_PRESSURE}, {}),
								("MAIN(1)_AND_NA_INTERMEDIATE(2)_Pump", MAIN_AND_NA_INTERMEDIATE_ADDRESS, "pump_mpc", ['pressure1', 'pressure2'], {'pressure1': MAIN_THRESHOLD_PRESSURE, 'pressure2':NA_INTERMEDIATE_THRESHOLD_PRESSURE}, {})],
								local_log_filename = "Vacuum_Log.csv")
	old_time = time.time()
	counter = 0
	local_logger_bool = True
	while(True):
		current_time = time.time()
		if(current_time - old_time > DELAY_TIME or current_time - old_time < 0):
			old_time = current_time 
			local_logger_bool = (counter % SAMPLES_PER_LOG == 0) 
			counter += 1
			if(PRINT_VALUES):
				print(my_monitor.monitor_once(log_local = local_logger_bool));
			else:
				my_monitor.monitor_once(log_local = local_logger_bool);


if __name__ == "__main__":
	main()

