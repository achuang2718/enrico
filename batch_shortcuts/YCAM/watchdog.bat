ECHO Starting enrico...
:: activate conda environment
CD C:\Users\Fermi1-YCAM\anaconda3\Scripts
CALL activate.bat
CALL conda.bat activate enrico

CD /d C:\Users\Fermi1-YCAM\Documents\Github\enrico
ECHO DID YOU CLOSE THE PREVIOUS INSTANCE OF THE WATCHDOG?
PAUSE
START python image_watchdog.py
ECHO image_watchdog.py started in a new window
START python analysis_logger.py
ECHO analysis_logger.py started in a new window