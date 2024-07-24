import numpy as np
import pandas as pd 
import matplotlib.pyplot as plt
import re
import os

def linearfit_pd(power, voltage):
    """
    return: numpy.array([m, b]) which defines linear fit y = m*x+b
    """
    fits = np.polyfit(voltage, power, 1)
    return fits

def get_calibration_params(df):
    NaMOT_ports = [k.split('_')[0] for k in df.columns if re.search('(.*)_mw',k)]
    df_fits = pd.DataFrame()
    for port in NaMOT_ports:
        fits = linearfit_pd(df[f'{port}_mw'],df[f'{port}_V'])
        df_fits[port] = fits
    df_fits.index = ['m','b']

    return df_fits

def show_fits(df, df_fits):
    fig, axes = plt.subplots(3,2)


    for port, ax in zip(df_fits.columns, axes.flat):
        func = np.poly1d(df_fits[port])
        volts = np.linspace(0, df[f'{port}_V'].max(), 100)
        powers = func(volts)
        ax.scatter(df[f'{port}_V'], df[f'{port}_mw'], color = 'red')
        ax.plot(volts, powers, color = 'blue')
        ax.grid(color='lightgray', alpha=0.8)
        ax.set_xlabel('Photo Detector Voltage [V]')
        ax.set_ylabel('Laser Power [mW]')
        ax.set_title(f'NaMOT Monitor PD Calibration: {port}')
    plt.tight_layout()
    plt.show()

if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    calibration_filename = 'MOT Monitor Calibration_2022-09-15.csv'
    date = re.search('\d(.*)\d',calibration_filename).group()
    df = pd.read_csv(calibration_filename)  
    df_fits = get_calibration_params(df)
    df_fits.to_csv(f'MOT Monitor Calibration Parameter Table_{date}.csv')
    show_fits(df,df_fits)



    
    