import requests
import pandas as pd
import time
from datetime import datetime, timedelta
from status_monitor import StatusMonitor

auth = requests.auth.HTTPDigestAuth('admin', 'admin')
SKIPROWS1, SKIPROWS2 = 29, 23
my_monitor = StatusMonitor(warning_interval_in_min = 0)
TRIGGER_TEMPERATURE = 50


def parse_dataqcsv(fname, skiprows):
    df = pd.read_csv(fname, skiprows=list(range(skiprows)))
    unnamed_columns = [col for col in df.columns if 'Unnamed:' in col]
    df = df.drop(unnamed_columns, axis=1)
    last_row = df.iloc[-1:]
    #sometimes the DATAQ file writing has not finished the last row,
    #so use the second to last instead
    if last_row.isnull().values.any():
        last_row = df.iloc[-2:-1]
    data_dict = {col: last_row[col].values[0] for col in last_row.columns
        if 'Date/Time' not in col}
    return data_dict

def trigger(data_dict, trigger_level = TRIGGER_TEMPERATURE):
	for key in data_dict:
		if data_dict[key] > trigger_level:
			warning_msg = key + ' temperature (deg C) is above threshold at ' + str(data_dict[key])
			my_monitor.warn_on_slack(warning_msg, annoying=True)

def construct_fnames(yesterday=False):
	now = datetime.now()
	if yesterday:
		now = datetime.now() - timedelta(days=1)
	date_str = now.strftime('%Y-%m-%d')
	fname1, fname2 = [date_str + time_str for time_str in ('T20-54-00.csv', 'T21-15-00.csv')]
	return fname1, fname2

def construct_urls(fname1, fname2):
	monitor1_IP = '192.168.1.224'
	monitor2_IP = '192.168.1.223'
	url1 = 'http://{IP}/data/files/local/{fname}'.format(IP = monitor1_IP, fname = fname1)
	url2 = 'http://{IP}/data/files/local/{fname}'.format(IP = monitor2_IP, fname = fname2)
	return url1, url2

def monitor_temperatures():
	def fetch_and_monitor(fname, url, skiprows):
		r = requests.get(url, auth = auth)
		data = r.content
		with open('dataq_logs/' + fname, 'wb') as f:
			f.write(data)
		data_dict = parse_dataqcsv('dataq_logs/' + fname, skiprows)
		print(data_dict)
		trigger(data_dict)
	while True:
		try:
			fname1, fname2 = construct_fnames()
			url1, url2 = construct_urls(fname1, fname2)
			fetch_and_monitor(fname1, url1, SKIPROWS1)
			fetch_and_monitor(fname2, url2, SKIPROWS2)
			time.sleep(5)
		except pd.errors.EmptyDataError:
			fname1, fname2 = construct_fnames(yesterday=True)
			url1, url2 = construct_urls(fname1, fname2)
			fetch_and_monitor(fname1, url1, SKIPROWS1)
			fetch_and_monitor(fname2, url2, SKIPROWS2)
			time.sleep(5)
		# fname1, fname2 = construct_fnames()
		# url1, url2 = construct_urls(fname1, fname2)
		# fetch_and_monitor(fname1, url1, SKIPROWS1)
		# fetch_and_monitor(fname2, url2, SKIPROWS2)
		# time.sleep(5)

monitor_temperatures()