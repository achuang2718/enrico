import subprocess
import os
import sys
main_path = os.path.abspath(os.path.join(__file__, '../..'))
sys.path.insert(0, main_path)
import enrico_bot

i = 0
while True:
    if i == 0:
        print('python keysight_lockdetector.py')
        p1 = subprocess.run('python keysight_lockdetector.py',
                            shell=True)
        enrico_bot.post_message('keysight_lockdetector.py restarted automatically.')
        print('\n restarting')
        i += 1
    else:
        p1 = subprocess.run('python keysight_lockdetector.py',
                            shell=True)