import numpy as np
from ps4824a_wrapper_blockmode_utils import Picoscope
from status_monitor import StatusMonitor
import datetime
import time
from utility_functions import get_newest_run_dict, time_diff_in_sec

class MOTPowerMonitor(StatusMonitor):
    def __init__(self, refresh_time = 5, **kwargs):
        StatusMonitor.__init__(self, **kwargs)
        self.scope = Picoscope(0, serial='HT379/040', verbose=True)
        #TODO: import scope   instead of hardcoding here
        self.channel_dict = {
            'A': {'channel_label': 'Trigger','channel_range_mv': 2000},            
            'B': {'channel_label': 'NaMOT_Top','channel_range_mv': 5000},
            'C': {'channel_label': 'NaMOT_Bottom','channel_range_mv': 2000},
            'D': {'channel_label': 'NaMOT_KSlowerWindow','channel_range_mv': 500},
            'E': {'channel_label': 'NaMOT_KSlower','channel_range_mv': 2000},
            'F': {'channel_label': 'NaMOT_NaSlowerWindow','channel_range_mv': 5000},
            'G': {'channel_label': 'NaMOT_NaSlower','channel_range_mv': 5000},                                                            
        }
        self._configure_picoscope(self.scope)
        self.refresh_time = refresh_time
    
    def _configure_picoscope(self, scope):
        for chl_idx, params in self.channel_dict.items():
            scope.setup_channel(chl_idx, channel_range_mv=params['channel_range_mv'])
        scope.setup_trigger('B', trigger_threshold_mv=200)
        scope.setup_block(block_size=100000, block_duration=1, pre_trigger_percent=0)
    
    def upload_to_breadboard(self):
        # matches backlog times to run_id times and writes (but not overwrites) closest log entry to breadboard
        try:
            run_dict = get_newest_run_dict(self.bc)
        except:
            print(traceback.format_exc())
        new_run_id = run_dict['run_id']
        time_diffs = np.array([time_diff_in_sec(
            run_dict['runtime'], backlog_time) for backlog_time in self.backlog])
        time_diffs[time_diffs < self.read_run_time_offset] = -np.infty
        min_idx = np.argmin(np.abs(time_diffs + self.read_run_time_offset))
        min_time_diff_from_ideal = (time_diffs[min_idx] +
                                    self.read_run_time_offset)
        if np.abs(min_time_diff_from_ideal) < self.max_time_diff_tolerance:
            print("Newest breadboard run_id {id} at time: ".format(id=str(run_dict['run_id']))
                  + str(run_dict['runtime']))
            closest_backlog_time = list(
                self.backlog.keys())[min_idx]
            dict_to_upload = self.backlog[closest_backlog_time]
            readout_exists_on_breadboard = False
            for value_name in dict_to_upload.keys():
                if value_name in run_dict:
                    readout_exists_on_breadboard = True
                    # print('{name} already exists for run_id {id} on breadboard.'.format(name=value_name,id=run_dict['run_id']))
            if not readout_exists_on_breadboard:
                resp = self.bc.add_instrument_readout_to_run(
                    new_run_id, dict_to_upload)
                if resp.status_code != 200:
                    warning_text = ('Error uploading {dict_to_upload} from {time_str} to run_id {id}. Error text: '.format(dict_to_upload=str(dict_to_upload),
                                                                                                                           reading=str(
                                                                                                                               value_to_upload),
                                                                                                                           time_str=str(
                                                                                                                               closest_backlog_time),
                                                                                                                           id=str(
                                                                                                                               new_run_id)
                                                                                                                           ) + resp.text)
                    self.warn_on_slack(warning_text)
        else:
            warning_text = 'Time difference {diff} sec between reading and latest breadboard entry exceeds max tolerance of {tol} sec. Check breadboard-cicero-client.'.format(
                diff=str(np.abs(min_time_diff_from_ideal)), tol=str(self.max_time_diff_tolerance))
            if np.abs(min_time_diff_from_ideal) != np.inf:
                self.warn_on_slack(warning_text)

    def main(self):
        with self.scope as scope:
            scope = self.scope
            while True:
                scope.run_block()
                scope_traces = scope.get_block_traces()
                time_now = datetime.datetime.today()
                mot_power_dict = {}
                for chl_idx, params in self.channel_dict.items():
                    label = params['channel_label']
                    if label == 'Trigger':
                        continue
                    trace = scope_traces[chl_idx]
                    mot_power_dict.update({f'{label}_mean_in_mv': np.mean(trace),
                                        f'{label}_std_in_mv': np.std(trace)})

                self.append_to_backlog(mot_power_dict, time_now=time_now)
                #hot fix sleep
                time.sleep(5)
                self.upload_to_breadboard() 
                time.sleep(self.refresh_time)
                print('\n\n')


if __name__ == '__main__':
    mot_power_monitor = MOTPowerMonitor(refresh_time=0, read_run_time_offset=-36, max_time_diff_tolerance=30)
    mot_power_monitor.main()