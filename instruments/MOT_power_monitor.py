import numpy as np
from ps4824a_wrapper_blockmode_utils import Picoscope
from status_monitor import StatusMonitor
import datetime
import time

class MOTPowerMonitor(StatusMonitor):
    def __init__(self, refresh_time = 5, **kwargs):
        StatusMonitor.__init__(self, **kwargs)
        self.scope = Picoscope(0, serial='HT379/040', verbose=True)
        #TODO: import scope   instead of hardcoding here
        self.channel_dict = {
            'A': {'channel_label': 'Trigger','channel_range_mv': 2000},            
            'B': {'channel_label': 'NaMOT_Top','channel_range_mv': 1000},
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
                self.upload_to_breadboard() 
                time.sleep(self.refresh_time)
                print('\n\n')


if __name__ == '__main__':
    mot_power_monitor = MOTPowerMonitor(refresh_time=0, read_run_time_offset=-36, max_time_diff_tolerance=30)
    mot_power_monitor.main()