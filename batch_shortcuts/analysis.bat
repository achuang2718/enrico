ECHO Starting enrico...
:: activate conda environment
CD /d C:\Users\Fermi\anaconda3\Scripts
CALL activate.bat

CD /d C:\Users\fermi\Documents\GitHub\enrico
ECHO DID YOU CLOSE THE PREVIOUS INSTANCE OF THE ANALYSIS?
PAUSE
START python analysis_logger.py
ECHO analysis_logger.py started in a new window