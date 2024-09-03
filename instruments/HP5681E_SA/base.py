"""

TODO
"""
import pyvisa 
import numpy as np 
import pyqtgraph as pg 
from simplevisa import HP856x
from pyqtgraph.Qt import QtCore

device = HP856x(0, 18)

win = pg.GraphicsLayoutWidget(show=True, title='test')
win.resize(1000,600)
pic = win.addPlot(title="Updating plot")
curve = pic.plot(pen='y')
data = device.showGraph()
ptr = 0
def update():
    global curve, data, ptr, pic
    curve.setData(data[ptr%10])
    if ptr == 0:
        pic.enableAutoRange('xy', False)  ## stop auto-scaling after the first data set is plotted
    ptr += 1
timer = QtCore.QTimer()
timer.timeout.connect(update)
timer.start(50)
pg.exec()