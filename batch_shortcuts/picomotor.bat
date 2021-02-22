ECHO Starting enrico...
:: activate conda environment
CD /d C:\Users\Fermi1\anaconda3\Scripts
CALL activate.bat

CD /d D:\Fermidata1\enrico\instruments
ECHO STARTING PICOMOTOR GUI
START python picomotor.py
ECHO picomotor python console started in a new window

