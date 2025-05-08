import pyvisa
import re
from PyQt5 import QtWidgets
from PyQt5.QtCore import QTimer
import pyqtgraph as pg
import sys
import csv
import time


class TemperatureLogger(QtWidgets.QMainWindow):
    """
    Barebone code for extracting temperature and resistance readings from LFI-3751 temperature controller (Wavelength Electronics)
    """

    def __init__(self, logging_interval, verbose=False):

        """
        args:
            -  logging_interval: in seconds
        """
        super().__init__()
        
        self.connect_device(visa_resource_name='ASRL5::INSTR')
        self.verbose = verbose
        
        # Setup the CSV file dialog
        self.filepath, _ = QtWidgets.QFileDialog.getSaveFileName(self, 'Save CSV', '', '*.csv')
        if not self.filepath:
            sys.exit("No file selected, exiting.")

        # Initialize CSV file
        with open(self.filepath, 'w', newline='') as csvfile:
            self.csv_writer = csv.writer(csvfile)
            self.csv_writer.writerow(["Timestamp", "Temperature [C]", "Resistance [kOhm]", "Current [A]"])

        # Setup the plot window
        self.plot_window = pg.GraphicsLayoutWidget()
        self.setCentralWidget(self.plot_window)

        # Create two vertically stacked plots
        self.temperature_plot = self.plot_window.addPlot(title="ULE cavity temperature [C]")
        self.plot_window.nextRow()  # Move to the next row before adding the second plot
        self.resistance_plot = self.plot_window.addPlot(title="ULE cavity thermistor resistance [kOhm]")
        self.plot_window.nextRow()  # Move to the next row before adding the second plot
        self.current_plot = self.plot_window.addPlot(title="ULE cavity TEC current [A]")

        # Create separate DateAxisItem instances
        time_axis_temperature = pg.DateAxisItem(orientation='bottom', format_string='%m-%d %H:%M:%S')
        time_axis_resistance = pg.DateAxisItem(orientation='bottom', format_string='%m-%d %H:%M:%S')
        time_axis_current = pg.DateAxisItem(orientation='bottom', format_string='%m-%d %H:%M:%S')
        
        # Set the DateAxisItem instances to the plots
        self.temperature_plot.setAxisItems({'bottom': time_axis_temperature})
        self.resistance_plot.setAxisItems({'bottom': time_axis_resistance})
        self.current_plot.setAxisItems({'bottom': time_axis_current})
        
        # Link the x-axes of the two plots
        self.resistance_plot.setXLink(self.temperature_plot)  # Link the x-axis of the two plots

        # Create scatter plots
        self.temperature_curve = self.temperature_plot.plot(pen=None, symbol='o', symbolBrush='r', name="Temperature")
        self.resistance_curve = self.resistance_plot.plot(pen=None, symbol='o', symbolBrush='b', name="Resistance")
        self.current_curve = self.current_plot.plot(pen=None, symbol='o', symbolBrush='y', name="Current")

        # Data buffers
        self.temperature_data = []
        self.resistance_data = []
        self.current_data = []
        self.timestamps = []

        # Setup the timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_data)
        self.timer.start(logging_interval*1000)

    def connect_device(self, visa_resource_name):
        try:
            rm = pyvisa.ResourceManager()
            self.device = rm.open_resource(visa_resource_name)
            self.device.baud_rate = 19200 # must be this value
            self.device.read_termination = '\r\n'
            self.device.write_termination = None

            model = self.query_device_model()
            firmware = self.query_device_firmware()
        except pyvisa.VisaIOError as e:
            print(f'VISA error occured. Try reconnecting the device.')
            raise e
        
        else:
            print(f'{model} connected. Running firmware version = {firmware}')

    def extract_data(self, response:str):
        """
        Semi-hardcoded. Tested only for temperature, resistance, and device id.
        """
        return response.strip()[9:17] 
    
    def query_temperature(self):
        response = str(self.device.query('!101101+000.00024'))
        response_clean = float(self.extract_data(response))
        if self.verbose:
            print(f'Temperature reading {response_clean}C')
        return response_clean
    
    def query_resistance(self):
        response = str(self.device.query('!101102+000.00027'))
        response_clean = float(self.extract_data(response))
        if self.verbose:
            print(f'Resistance reading {response_clean}kOhm')
        return response_clean
    
    def query_current(self):
        response = str(self.device.query('!101105+000.00020'))
        response_clean = float(self.extract_data(response))
        if self.verbose:
            print(f'Resistance reading {response_clean}A')
        return response_clean
    
    def query_device_model(self):
        return str(self.extract_data(self.device.query('!101157+000.00027')))
    
    def query_device_firmware(self):
        return str(self.extract_data(self.device.query('!101156+000.00026')))
                    

    def update_data(self):
        try:
            temperature = self.query_temperature()
            resistance = self.query_resistance()
            current = self.query_current()
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

            # Save to CSV
            with open(self.filepath, 'a', newline='') as csvfile:
                self.csv_writer = csv.writer(csvfile)
                self.csv_writer.writerow([timestamp, temperature, resistance, current])

            # Update the data buffers
            self.temperature_data.append(temperature)
            self.resistance_data.append(resistance)
            self.current_data.append(current)
            self.timestamps.append(len(self.timestamps))

            # Update the plot
            self.temperature_curve.setData(self.timestamps, self.temperature_data)
            self.resistance_curve.setData(self.timestamps, self.resistance_data)
            self.current_curve.setData(self.timestamps, self.current_data)
        except Exception as e:
            print(f"An error occurred: {e}")

    def closeEvent(self, event):
        # Stop the timer to prevent any more updates
        self.timer.stop()
        
        # Close the connection to the device
        if self.device is not None:
            self.device.close()
        
        # Allow the event to propagate (this closes the window)
        event.accept()



# Run the application
if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    main_window = TemperatureLogger(logging_interval=5, verbose=True)  # Set the interval in seconds
    main_window.show()
    sys.exit(app.exec_())