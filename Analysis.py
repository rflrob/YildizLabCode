#!/usr/bin/env python
# encoding: utf-8
"""
Analysis.py

Created by Peter Combs on 2009-11-17.
Based on Adam Cohen's Matlab code for two color reconciling.

Copyright (c) 2009 UC Berkeley. All rights reserved.
"""
#from pylab import *

import sys, os, Image

import numpy as np
from numpy import array, zeros, histogram, concatenate, sqrt, shape, \
	meshgrid, ravel, exp, arange, mgrid, linspace, random, mean, \
	NaN, reshape, median, sum, cumsum, diff
import numpy.numarray.nd_image as ndi
import scipy.interpolate as interp
import scipy.linalg as la
import scipy.optimize as optimize
from scipy.special import jn as bessel
from Mapping import *

from fitgauss import fitgauss

from pyfits import open as pfopen

from pylab import figure, colorbar, title, plot, savefig, show, legend, \
	imshow, pcolor, cm, ion

from time import time
from multiprocessing import Pool

box1_default = (slice(0,256),slice(0,512))
box2_default = (slice(256, 512), slice(0, 512))

def main():
	from scipy.io import loadmat
	from getopt import getopt
	
	try:
		optlist, args = getopt(sys.argv[1:], 'b:e:s:n:')
		print optlist, args
	except:
		sys.exit(2)
		
	matfile = 'big.mat'
	begin = 1
	end = 36
	step = 1
	n = None
	
	for o,a in optlist:
		if o in ('-b'): 
			begin = int(a)
		elif o in ('-e'): 
			end = int(a)+1
		elif o in ('-s'): 
			step = int(a)
		elif o in ('-n'):
			n = int(a)
		else: 
			assert False, "Unhandled option"
	
	if len(args) > 0:
		matfile = args[0]
	
	
	data = loadmat(matfile, struct_as_record = False, squeeze_me = True)
	xl = data['xl']
	yl = data['yl']
	xr = data['xr']
	yr = data['yr']
	
	
	xlo, xhi = middle_percent(xl, .2)
	ylo, yhi = middle_percent(yl, .2)
	sel = (xlo < xl) * (xl < xhi) *  (ylo < yl) * (yl < yhi)
	
	print "Starting with %d points" % len(xl)
	xl = xl[sel]
	yl = yl[sel]
	xr = xr[sel]
	yr = yr[sel]
	print "Cropping down to %d points" % len(xl)
	
	if n == None: n = 0.1 * sqrt(len(xl))
	
	make_spline_mesh(xl, yl, xr, yr, n)	
	tres = zeros(end)
	rmss = zeros(end)
	rmsg = zeros(end)
	for i in range(begin, end, step):
		good, tre = sample_target_registration_error(xl, yl, xr, yr,i, n=5)
		if tre < 20:
			tres[i] = tre
			mapping = makeLSQspline(xl, yl, xr, yr)
		
			xn, yn = mapping(xr, yr)
			rmss[i] = sqrt(mean((xn - xl)**2 + (yn - yl)**2) )
		else:
			tres[i] = NaN
			rmss[i] = NaN
		
		figure()
		plot(arange(len(tres)), tres, 'ro-', label='TRE')
		plot(arange(len(rmss)), rmss, 'gx--',label='RMS')
		title("Errors on %d points" % len(xl))
		legend()
		savefig('sTREvsNKnots.pdf')
		print "just finished ", i
		
	show()
	print "TREs\t\tRMSs\t\tgood RMSs"
	for i in range(len(tres)):
		print "%f\t\t%f\t\t%f" % (tres[i], rmss[i], rmsg[i])
	
	mapping = makeLSQspline(xl[good], yl[good], xr[good], yr[good])
	
	xn, yn = mapping(xr[good], yr[good])
	
	rms = sqrt(mean((xn-xl[good])**2 + (yn - yl[good])**2))
	
	print "RMS Error with best points only: ", rms
	sys.stderr.write("RMS Error with best points only: %f\n" % rms)
	
	target_registration_error(xl[good], yl[good], xr[good], yr[good])


def split(img, bgimg = None, box1 = box1_default, box2 = box2_default):
	if bgimg != None:
		img -= bgimg
		
	imgl = img[box1]
	imgr = img[box2]
	
	imgl -= imgl.min()
	imgr -= imgr.min()
	
	imgl *= float(imgr.max())/imgl.max()
	return imgl, imgr

def imread(fname):
	ext = os.path.splitext(fname)[1]
	try:
		if ext == '.tif':
			imf = Image.open(fname)
			img = np.reshape(imf.getdata(), imf.size)
		elif ext == ".fits":
			img = pfopen(fname)[0].data
		else:
			sys.stderr.write("Unrecognized file type '%s'!\n" % ext)
			sys.exit(10)
	except:
		print "Had a problem with ", fname
	return img
	
def loadsplit(fname, bgimg = None, box1 = box1_default, box2 = box2_default):
	"""function [imgl imgr] = loadsplit(fname, imstart,imstop, box1, box2)
	loads a single FITS image and splits it into two pieces.
	fname: full path and filename for the input.
	box1: 2 element tuple of slices.
	box2: vector specifying the second sub-image.
	The boxes shouldn't contain dark borders around the edges of the images.
	Typically:
	box1 = (slice(18,247),slice(7,506))
	box2 = (slice(276, 505), slice(7, 506))
	"""
	
	img = imread(fname)
	return split(img, bgimg, box1, box2)


def stretch(image):
	""" Rescales an image to the range [0, 1]"""
	m = image.min()
	return (image - m)/(image.max() - float(m))


def otsu_threshold(image):
	""" Returns the optimal threshold, as calculated using Otsu's Algorithm on 
	the data squeezed into 8 bits
	"""
	
	tick = time()
	m = image.min()
	M = image.max()
	image = 255 * (image - m)/(M-m) 
	hgram, edges = histogram(image.flat, bins = arange(256))
	
	num_b = 0
	num_a = len(image.flat)
	total_b = 0
	total_a = float(image.sum())
	varBetween = zeros(len(hgram))
	
	for t in range(len(hgram)):
		num_b += hgram[t]
		num_a -= hgram[t]
		total_b += t * hgram[t]
		total_a -= t * hgram[t]
		mu_b = total_b/(num_b+1e-13)
		mu_a = total_a/(num_a+1e-13)
		varBetween[t] = (num_b * num_a) * (mu_b - mu_a)**2
	
	threshold = varBetween.argmax()
	
	return threshold * (M - m)/256.0 + m


def strel():
	"""Creates a disk-shaped structuring element. """
	return array([[0, 0, 1, 1, 1, 1, 1, 0, 0],
				[0, 1, 1, 1, 1, 1, 1, 1, 0],
				[1, 1, 1, 1, 1, 1, 1, 1, 1],
				[1, 1, 1, 1, 1, 1, 1, 1, 1],
				[1, 1, 1, 1, 1, 1, 1, 1, 1],
				[1, 1, 1, 1, 1, 1, 1, 1, 1],
				[1, 1, 1, 1, 1, 1, 1, 1, 1],
			[0, 1, 1, 1, 1, 1, 1, 1, 0],
			[0, 0, 1, 1, 1, 1, 1, 0, 0]    ])


def mpt(im_in, thresh = 1.0, im_start=0, im_end = None, **kwargs):
	"""Multiple Particle tracking.  
	Using the stacked image from im_in, finds particles and localizes them 
	with the fitting2d function
		
	Return
	------
	a list of dictionaries, each of which contains keys whose values are:
		'numspots':	Number of spots detected
		'x2': 		array of x coordinates of the spots
		'y2': 		array of y coordinates of the spots
		'varx': 	array of width of the fit in x
		'vary': 	array of width of the fit in y
		'offset': 	array of level of the background
		'amp':		array of height of the fit above background
		'exits':	array of return values from the fitting
		 
	Optional Keyword Arguments
	--------------------------
	DEBUG : Outputs debugging information, especially graphs; Default is False
	smooth : use a gaussian blur to smooth the data (?why); Default is False
	abs_thresh : 
	
	"""
	
	smooth = False
	abs_thresh = False
	DEBUG = False
	padding = 7
	
	for key in kwargs:
		if key == "smooth": smooth = kwargs[key]
		elif key == "abs_thresh": abs_thresh = kwargs[key]
		elif key == "frame_num" : frame_num = kwargs[key]
		elif key == "DEBUG": DEBUG = kwargs[key]
		elif key == "padding": padding = kwargs[key]
		
	
	if(im_end == None): 
		if len(shape(im_in)) == 3: 
			im_end = shape(im_in)[2]
		else: 
			# Reshape to a stack if only a 1-D image
			im_end = 1 
			im_in = reshape(im_in, (shape(im_in)[0], shape(im_in)[1], 1))
	
	coords = [None]*(im_end - im_start)
	for i in range(im_start, im_end):
		if DEBUG > 0: print i, "of ", im_end - im_start
		A = im_in[:,:,i]
		
		if smooth: bA = ndi.gaussian_filter(A, 2)
		else: bA = A
		
		if abs_thresh: 
			T = 1
		else: 
			T = otsu_threshold(bA)
		
		
		Amask = bA > (T * thresh)
		
		l, n = ndi.label(Amask)
		
		if DEBUG > 1:
			ion()
			
			figure(1138)
			imshow(Amask*bA, cmap = cm.gray)
			colorbar()
			title('Mask: Foo > %f' % (T * thresh))
			print T
			print thresh
			print "Number of spots found: ", n
		
		if n == 0:
			x2 = []
			y2 = []
			varx = []
			vary = []
			amp = []
			offset = []
			exits = []
		else:
			D = ndi.find_objects(l)    # Generates a list of slices
			
			# Set up empty variables
			x2 = zeros(n)
			y2 = zeros(n)
			varx = zeros(n)
			vary = zeros(n)
			amp = zeros(n)
			offset = zeros(n)
			exits = zeros(n)
			
			
			for j in range(n):
				row, col = D[j]

                # Make sure fitbox is legal
				rstart = max(0, row.start - padding)
				rend = min(shape(im_in)[0]-1, row.stop + padding)
				cstart = max(0, col.start - padding)
				cend = min(shape(im_in)[1]-1, col.stop + padding)
				
                # Take fitbox and subtract background
				B = im_in[rstart:rend, cstart:cend, i]
				B = B - B.min()
				
                # Coordinates for fitting
				dy, dx = mgrid[rstart:rend, cstart:cend]
								
				if DEBUG > 2:
					figure()
					pcolor(dx, dy, B)
					colorbar()
				try:
					fit, exit = fit2d(dx, dy, B)
					x2[j] = fit[0]
					y2[j] = fit[1]
					varx[j] = fit[2]
					vary[j] = fit[3]
					offset[j] = fit[4]
					amp[j] = fit[5]
					exits[j] = exit

                    # If fit is too close to the edge of the frame, then ignore it
                    if not (padding < x2[j] < shape(im_in)[0] - padding) \
                       or not (padding < y2[j] < shape(im_in)[1] - padding):
                        x2[j] = float("nan")
                        y2[j] = float("nan")
                        exits[j] = -1

					if DEBUG > 1:
						print "Fitted a point at:", fit
				except ValueError, err:
					print "Value error", err
					exits[j] = -1138
		coords[i] = {'x2': x2, 'y2': y2, 'varx': varx, 'vary': vary, 
				'offset': offset, 'amp': amp, 'exits': exits, 'numspots': n}
		if DEBUG > 1:
			figure(1138)
			plot(x2, y2, 'rx')
			sys.stderr.write(str(coords[i]) + '\n')
	return coords


def gaussian(center_x, center_y, width_x, width_y, offset, height):
    """Returns a gaussian function with the given parameters"""
    width_x = float(width_x)
    width_y = float(width_y)
    return lambda x,y: height*exp(-(((center_x-x)/width_x)**2 \
				+ ((center_y-y)/width_y)**2)/2) + offset



def airy(center_x, center_y, widthx, widthy, offset, height):
	"""Returns an airy disc function with the given parameters"""
	def airy_func(x,y):
		"A function to fit the Airy Disk for the given input"
		X = sqrt((x - center_x)**2/widthx + (y - center_y)**2/widthy)
		return offset + height * (bessel(1,X)/(X+1e-6)) **2
	return airy_func


def fit2d(xs, ys, data, estimate = None, fcn = None):
	"""Finds the best parameters for a gaussian distribution.  Parameters are 
	in the order:
	center_x, center_y, width_x, width_y, offset, height
	"""
	
	if estimate == None:
		estimate = zeros(6)
		estimate[0] = sum(xs * data)/ float(sum(data)) # Centroid
		estimate[1] = sum(ys * data) / float(sum(data))
		estimate[2] = 1.3			# Empirically determined
		estimate[3] = 1.3			
		estimate[4] = float(data.min())
		estimate[5] = float(data.max() - data.min())
	
	if fcn == None:
		fcn = gaussian
	errorfunction = lambda p: ravel(fcn(*p)(*(xs, ys)) - data)

	p, c,d, mesg, success = optimize.leastsq(errorfunction, estimate, full_output = True,  ftol=1e-3)
	
	return p, success


def findpairs(imleft, imright, thresh=1.0, radius=15, DEBUG = False, abs_thresh = False, frame_num = 0):
	""" finds pairs of particles in a stack of images from the dual-viewer 
	
	Returns
	-------
	pairs: list
		a list containing tuples of (xl, yl, xr, yr)
		
	Parameters
	----------
	imleft : array-like
		the left hand image stored in a numpy array
	imright : array-like 
		the right hand image stored in a numpy array
	thresh : double, optional
		The threshold level for finding particles.
	radius : double, optional
		The radius around a point to consider another point a "match".
	DEBUG : boolean, optional
		Print debugging statments/show images along the way.
	"""
	
	# Find points on the two images
	coordsl = mpt(imleft, thresh, abs_thresh = abs_thresh, smooth=False, DEBUG=DEBUG)[0]
	coordsr = mpt(imright, thresh, abs_thresh = abs_thresh, smooth=False, DEBUG=DEBUG)[0]

	pairs = []
	
	if DEBUG > 0:
		sys.stderr.write('%d spots on left\n' %coordsl['numspots'])
		sys.stderr.write('%d spots on right\n' %coordsr['numspots'])
	
	for i in range(coordsl['numspots']):
		for j in range(coordsr['numspots']):
			xl = coordsl['x2'][i]
			yl = coordsl['y2'][i]
			varxl = coordsl['varx'][i]
			varyl = coordsl['vary'][i]
			ampl = coordsl['amp'][i]
			xr = coordsr['x2'][j]
			yr = coordsr['y2'][j]
			varxr = coordsr['varx'][j]
			varyr = coordsr['vary'][j]
			ampr = coordsr['amp'][j]
			
			# If the distance is within tolerance, add data to the list of pairs
			delta = sqrt((xl - xr)**2 + (yl - yr)**2)
			if delta < radius:
				# Calculate a (possibly bullshit) estimate of the error.
				el = sqrt((varxl**2 + varyl**2)/ampl)
				er = sqrt((varyr**2 + varyr**2)/ampr)
				pairs.append((xl + box1_default[1].start+1, 512-(yl + box1_default[0].start), 
					      varxl, varyl, el, 
					      xr + box2_default[1].start+1, 512-(yr + box2_default[0].start), 
					      varxr, varyr, er, frame_num))
				# The massaging to xl, yl, xr, and yr is to make the output match WHTrack
				if DEBUG > 0:
					sys.stderr.write('Paired spots %d and %d'%(i,j))
		
	return pairs
	

def make_spline_mesh(xl, yl, xr, yr, num = 30, sampling=5, mapping = None):
	"""Makes spline fit of the given order, then draws a mesh representing 
	that spline fit
	"""	
	
	xs, ys = meshgrid(linspace(xl.min()+10, xl.max() - 10, num = sampling*num), 
				linspace(yl.min()+10, yl.max()-10, num = sampling*num))

	if mapping == None:	
		mapping = makeLSQspline(xl, yl, xr, yr, num)
	xn, yn = mapping(xs.ravel(), ys.ravel())
	xn = reshape(xn, shape(xs))
	yn = reshape(yn, shape(ys))
		
	for i in range(num):
		plot(xn[:,i], yn[:,i], 'r-')
		plot(xn[i,:], yn[i,:], 'r-')
	savefig('foobar.png')
	show()

	
def make_reg_mesh(xl, yl, xr, yr, order=2):
	""" One way of attempting to visualize a regression between the two sets"""
	xs, ys = meshgrid(linspace(xl.min(), xl.max()), 
			linspace(yl.min(), yl.max()))
	mapping = makeregression(xl, yl, xr, yr, order=order)
	xn, yn = mapping(xs.flatten(), ys.flatten())
	plot(xn.flatten(), yn.flatten(), ',g', label='Regression')
	savefig('foobar.png')



def target_registration_error(xl, yl, xr, yr, param=None):
	"""calculates the Target Registration Error
	 by setting aside each coordinate pair, calculating a 2nd order polynomial
	 fit from the right channel onto the left channel, then finding the error
	 of the un-set point.  The mean of these errors is calculated and returned.

	 WARNING: Runs in O(n^3) time.  
	"""
	
	from time import time
	tick = time()
	elist = zeros(len(xl))
	for i in range(len(xl)):
		xl_d = concatenate((xl[0:i], xl[i+1:]))
		yl_d = concatenate((yl[0:i], yl[i+1:]))
		xr_d = concatenate((xr[0:i], xr[i+1:]))
		yr_d = concatenate((yr[0:i], yr[i+1:]))
		mapping = makeLSQspline(xl, yl, xr, yr, param)
		xn, yn = mapping(xr[i], yr[i])
		#print "xn\t",xn, "yn\t",yn, 
		elist[i] = sqrt((xl[i] - xn)**2 + (yl[i] - yn)**2)
		#print "e\t", elist[i]
		if (i % 100 == 0): sys.stderr.write('%d\n'%i)
	print "\n\ntime: ", time()-tick
	print "TRE: ", elist.mean()
	
	return elist < (4*median(elist)), elist.mean()


def sample_target_registration_error(xl, yl, xr, yr, 
		param=None, frac=.1, n = 100):
		"""Samples the Target Registration Error
		 by setting aside frac*len(xl) pairs, calculating a 2nd order 
		 polynomial fit from the right channel onto the left channel, 
		 then finding the rms error of the un-set points.  This 
		 process is repeated n times, and the mean of these errors 
		 is calculated and returned
		"""

		from time import time
		tick = time()
		elist = zeros(n)
		elist2 = zeros(len(xl))
		for i in range(n):
			sel = random.random(len(xl)) > frac
			xl_d = xl[sel]
			yl_d = yl[sel]
			xr_d = xr[sel]
			yr_d = yr[sel]
			mapping = makeLSQspline(xl_d, yl_d, xr_d, yr_d, param)
			xn, yn = mapping(xr[~sel], yr[~sel])
			elist[i] = mean(sqrt((xl[~sel] - xn)**2 + (yl[~sel] - yn)**2))
			elist2[~sel]+= sqrt((xl[~sel] - xn)**2 + (yl[~sel] - yn)**2)
			if (i % 100 == 0): sys.stderr.write('%d\n'%i)
		print "\n\ntime: ", time()-tick
		print "TRE: ", elist.mean()
		print "Avg Error: ", (elist2/(frac*n)).mean()

		return elist2 < (4*median(elist2)), elist.mean()


def middle_percent(points, frac):
	"""Returns the values between which 1-frac of the data lies."""
	

	sorted_points = sorted(points)
	
	hi = 1 - frac/2.0
	lo = frac/2.0
	
	return sorted_points[int(lo*len(points))],sorted_points[int(hi*len(points))-1]
	


if __name__ == '__main__':
	main()

