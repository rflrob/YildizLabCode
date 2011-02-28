import cPickle as pickle, os
import numpy as np, scipy.linalg as la, scipy.interpolate as interp

def loadmapping(basename):
	"""docstring for loadmapping"""
	if os.path.isfile(basename):
		bothfile = open(basename, 'rb')
		filetype = pickle.load(bothfile)
		if filetype == "V1-spline":
			xspline = pickle.load(bothfile)
			yspline = pickle.load(bothfile)
		if filetype == "V1-reg":
			order = pickle.load(bothfile)
			xcoeffs = pickle.load(bothfile)
			ycoeffs = pickle.load(bothfile)
			
			if not (len(xcoeffs) == len(ycoeffs) == (order+1) * (order+2) / 2):
				raise TypeError('Regression in "%s" is badly formed' % basename)
	else:
		xfile = open(basename + '_x')
		yfile = open(basename + '_y')
		xspline = pickle.load(xfile)
		yspline = pickle.load(yfile)
		filetype = "V0-spline"
	if "spline" in filetype:
		def mapping(xr, yr):
			return xspline.ev(xr, yr), yspline.ev(xr, yr)
	elif "reg" in filetype:
		
		def mapping(xr, yr):
			k = 0
			xl = 0
			yl = 0
			for i in range(order+1):
				for j in range(i+1):
					xl += xcoeffs[k] * xr**(i-j) * yr**j
					yl += ycoeffs[k] * xr**(i-j) * yr**j
					k += 1
			return xl, yl
	else:
		raise TypeError('File "%s" does not seem to contain any valid maps' 
							% basename)
	return mapping



def makeregression(xl, yl, xr, yr, order=2, savefile = None):
	"""Returns a function map, for mapping the right image onto the left, 
	using a linear regression of specified order
	Usage: 
	  mapping = makemap(xl, yl, xr, yr)
	  xl_mapped, yl_mapped = mapping(xr, yr)

	"""

	regvar = np.zeros((len(xl), (order+1)*(order+2)/2))

	k = 0
	for i in range(order+1):
		for j in range(i+1):
			regvar[:,k] = xr**(i-j) * yr**j
			k+=1

	xcoeffs = la.lstsq(regvar, xl)[0]
	ycoeffs = la.lstsq(regvar, yl)[0]
	
	if savefile:
		print savefile
		savefile = '%s_%d' % (savefile, order)
		print "Opening the file '%s'" % savefile
		outfile = open(savefile, 'wb')
		pickle.dump("V1-reg", outfile)
		pickle.dump(order, outfile)
		pickle.dump(xcoeffs, outfile)
		pickle.dump(ycoeffs, outfile)
	
	def mapping(xr, yr):
		""" A mapping function for taking the right image onto the left, returns x,y"""
		k = 0
		xl = 0
		yl = 0
		for i in range(order+1):
			for j in range(i+1):
				xl += xcoeffs[k] * xr**(i-j) * yr**j
				yl += ycoeffs[k] * xr**(i-j) * yr**j
				k += 1
		return xl, yl
	return mapping


def makesinglespline(args):
	return interp.LSQBivariateSpline(*args)


def makeLSQspline(xl, yl, xr, yr, n=20, savefile = None, multi = True):
	"""Returns a fitting function for taking the right channel onto the left"""

	if n == None:
		n = 20

	xmin = min(xr)
	xmax = max(xr)
	ymin = min(yr)
	ymax = max(yr)

	#print "xrange: ", xmin, xmax, '\t', "yrange: ", ymin, ymax

	#yknots, xknots = mgrid[ymin:ymax:10j, xmin:xmax:10j]

	s = 0
	xknots = np.linspace(xmin-s, xmax+s, n)
	yknots = np.linspace(ymin-s, ymax+s, n)

	print "X Knots: ", xknots, 
	print "Why Nots: ", yknots

	if multi:
		import multiprocessing as mp
		p = mp.Pool(processes = 2)
		[xspline, yspline] = p.map(makesinglespline, \
					zip([xr]*2, [yr]*2, [xl, yl], [xknots]*2, [yknots]*2))
	else:
		xspline = interp.LSQBivariateSpline(xr, yr, xl, xknots, yknots)
		yspline = interp.LSQBivariateSpline(xr, yr, yl, xknots, yknots)

	if savefile:

		# Old version of the pickling code.
		#print "Opening %s and %s" % (savefile + '_%d_x'%n, savefile + '_%d_y'%n)
		#xfile = open(savefile + '_%d_x'%n, 'w')
		#yfile = open(savefile + '_%d_y'%n, 'w')
		#cPickle.dump(xspline, xfile)
		#cPickle.dump(yspline, yfile)
		print n, str(n), type(n)
		print "Opening just the file %s" % (savefile+"_"+str(n))
		bothfile = open(savefile + "_" + str(n), 'wb')
		pickle.dump('V1-spline', bothfile)
		pickle.dump(xspline, bothfile)
		pickle.dump(yspline, bothfile)

	def mapping(xr, yr):
		""" Maps coordinates onto the left channel"""
		xl = xspline.ev(xr, yr)
		yl = yspline.ev(xr, yr)
		return xl, yl
	mapping.xspline = xspline
	mapping.yspline = yspline
	mapping.maptype = "LSQspline"
	return mapping
