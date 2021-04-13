ECHO Starting enrico...
:: activate conda environment
CD /d C:\Users\Fermi1\anaconda3\Scripts
CALL activate.bat

CD /d D:\Fermidata1\enrico
START python analysis_logger.py zd D:\Fermidata1\enrico\images\ False
ECHO Analyzing and discarding images in background

