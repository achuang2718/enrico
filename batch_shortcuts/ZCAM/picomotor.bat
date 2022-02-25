ECHO Starting enrico...
:: activate conda environment
CD C:\Users\ZCAM-Fermi1\anaconda3\Scripts
CALL activate.bat
CALL conda.bat activate enrico

CD C:\Users\ZCAM-Fermi1\Documents\Github\enrico\instruments
ECHO STARTING PICOMOTOR GUI
START python picomotor.py
ECHO picomotor python console started in a new window

