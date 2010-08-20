from scipy.io import loadmat, savemat
import sys
from os.path import basename
from math import ceil

fname = '.'.join(basename(sys.argv[-1]).split('.')[:-1])
D = loadmat(sys.argv[-1], squeeze_me = True, struct_as_record = True)

xld = D['xl']; yld = D['yl']; xrd = D['xr']; yrd = D['yr']
varl = D['varxl']; varr = D['varxr']

for xlo in range(0, ceil(xld.max()), 100):
	for ylo in range(0, ceil(yld.max()), 100):
		xhi = xlo + 100
		yhi = ylo + 100
		sel = (xlo < xrd) * (xrd < xhi) * (ylo < yrd) * (yrd < yhi)
		savemat('%s_%d_%d'%(fname, xlo, ylo), \
			{'xl': xld[sel], 'yl' : yld[sel], 'xr': xrd[sel], 'yr' : yrd[sel], \
			'varxl' : varl[sel], 'varxr': varr[sel]}, oned_as = 'row')