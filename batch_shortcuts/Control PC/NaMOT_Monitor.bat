ECHO Starting enrico...
:: activate conda environment
CD /d D:\Anaconda3\Scripts
CALL activate.bat
CALL conda.bat activate enrico

CD /d C:\Users\Fermi1\Documents\GitHub\enrico\instruments
ECHO DID YOU CLOSE THE PREVIOUS INSTANCE OF THE PICOSCOPE?
PAUSE
START python MOT_power_monitor.py
ECHO MOT_power_monitor.py started in a new window