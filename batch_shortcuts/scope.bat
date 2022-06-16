:: activate conda environment
CD /d C:\Users\fermi\anaconda3\Scripts
CALL activate.bat

CD /d C:\Users\fermi\Documents\GitHub\enrico\instruments
ECHO DID YOU NAME THE SCOPE CHANNELS in enrico/instruments/scope_config.json?
PAUSE
START python keysight_lockdetector_autorestart.py