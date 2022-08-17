from keysight_scope import LockDetector, scope_visa_addresses, load_scopeconfig, Oscilloscope
import os
import sys
main_path = os.path.abspath(os.path.join(__file__, '../..'))
sys.path.insert(0, main_path)
import enrico_bot
import numpy as np
import traceback

SCOPE_NAME = 'near control PC'

def load_channel_names(SCOPE_NAME):
    lock_channels = load_scopeconfig()['channel_names'][SCOPE_NAME]
    lock_channels = {int(key):lock_channels[key] for key in lock_channels}
    return lock_channels
lock_channels = load_channel_names(SCOPE_NAME)

lockdetector_control_PC = LockDetector(visa_address=scope_visa_addresses[SCOPE_NAME],
                            lock_channels=lock_channels, read_run_time_offset=-10) 
                            #read_run_time_offset set to negative value of ~half time between shots,
                            #since scope may read out trace *before* the associated run_id is created on breadboard.

if __name__ == '__main__':
    try:
        lockdetector_control_PC.main()
    except Exception as e:
        print(traceback.format_exc())
        enrico_bot.post_message('restart keysight_lockdetector.py' + sys.exc_info()[1])

