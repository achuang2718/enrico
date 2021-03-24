from vacuum_monitor import VacuumMonitor
import time

NA_OVEN_ADDRESS = "COM9"
K_INTERMEDIATE_ADDRESS = "COM10"
MAIN_AND_NA_INTERMEDIATE_ADDRESS = "COM11"
K_OVEN_ADDRESS = "COM12"

NA_OVEN_THRESHOLD_PRESSURE = 1e-7
K_OVEN_THRESHOLD_PRESSURE = 1e-5
MAIN_THRESHOLD_PRESSURE = 1e-10
NA_INTERMEDIATE_THRESHOLD_PRESSURE = 1e-9
K_INTERMEDIATE_THRESHOLD_PRESSURE = 1e-8

DELAY_TIME = 5
SAMPLES_PER_LOG = 12

PRINT_VALUES = True

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

