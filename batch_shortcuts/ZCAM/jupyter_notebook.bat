:: activate conda environment
ECHO Starting enrico...
:: activate conda environment
CD C:\Users\ZCAM-Fermi1\anaconda3\Scripts
CALL activate.bat
CALL conda.bat activate enrico

CD /d Z:
jupyter notebook
PAUSE