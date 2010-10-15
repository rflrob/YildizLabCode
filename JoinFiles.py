from scipy.io import loadmat, savemat
from numpy import maximum, shape, array, zeros
import sys

allData = {}

for fname in sys.argv[1:]:
	print "Loading %s" % fname
	D = loadmat(fname, squeeze_me = True, struct_as_record = True)
	print D.keys()
	for key in D.keys():#['xl', 'yl', 'xr', 'yr', 'varxl', 'varxr']:
		print "Working up Key: ", key
		if key[0] == "_": continue
		if allData.has_key(key):
			if D[key].ndim == 1:
				allData[key].extend(list(D[key]))
			elif D[key].ndim == 2:
				finalshape = maximum(shape(allData[key]), shape(D[key]))
				a = zeros(finalshape)
				b = zeros(finalshape)
				for r in range(shape(allData[key])[0]):
					for c in range(shape(allData[key])[1]):
						a[r,c] = allData[key][r,c]
				for r in range(shape(D[key])[0]):
					for c in range(shape(D[key])[1]):
						b[r,c] = D[key][r,c]
				
				allData[key] = maximum(a, b)
				
		else:
			if D[key].ndim == 1:
				allData[key] = list(D[key])
			else:
				allData[key] = D[key]

len(allData[allData.keys()[0]])
outfile = raw_input('What do you want to name the saved file? ')

savemat(outfile, allData)