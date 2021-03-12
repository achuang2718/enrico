from keysight_scope import LockDetector, scope_visa_addresses, load_scopeconfig
import os
import sys
main_path = os.path.abspath(os.path.join(__file__, '../..'))
sys.path.insert(0, main_path)
import enrico_bot

SCOPE_NAME = 'near laser tables'

def load_channel_names(SCOPE_NAME):
    lock_channels = load_scopeconfig()['channel_names'][SCOPE_NAME]
    lock_channels = {int(key):lock_channels[key] for key in lock_channels}
    return lock_channels
lock_channels = load_channel_names(SCOPE_NAME)

lockdetector = LockDetector(visa_address=scope_visa_addresses[SCOPE_NAME],
                            lock_channels=lock_channels)
if __name__ == '__main__':
    try:
        lockdetector.main()
    except:
        print('error')
        pass
        # enrico_bot.post_message('restart keysight_lockdetector.py' + sys.exc_info()[1])