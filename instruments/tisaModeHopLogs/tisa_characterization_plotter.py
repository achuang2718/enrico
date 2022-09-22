# plot data from Solstis.characterize_mode_hop

import pandas as pd
import matplotlib.pyplot as plt
import time

while True:
	df = pd.read_csv('tisa_characterization.log', header=None)
	plt.subplot(211)
	plt.cla()
	plt.plot((df[2]  - 360.) * 1e3, label = 'w/o etalon lock')
	plt.plot((df[3]  - 360.) * 1e3, label = 'w/ lock')
	plt.legend(loc='best')
	plt.ylabel('freq (GHz) + 360THz')
	plt.subplot(212)
	plt.cla()
	plt.plot(df[1])
	plt.ylabel('etalon tune setting (%)')
	plt.savefig('tisa.png')
	plt.show()
	plt.close('all')
	time.sleep(10)