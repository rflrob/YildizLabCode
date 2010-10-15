"""
Processing.py

Created by Peter Combs (peter.combs@berkeley.edu) on 2009-12-10
"""

USAGE = """python %s --specification='pattern' [options]
Options and Arguments:
-b	: Specify the location for a particular background image
-B n	: Generate a background image from n randomly selected images in the glob pattern
-c n	: Cap the number of input images at n
-e n	: Specify the image to end before
-o file	: Specify a file to save the output in.  The .mat suffix is optional
-p	: Profiling mode supresses display of points at the end of the run.
-q	: Use a queue to do processing instead of a pool (# may not work as of 01/10/2010)
-s n	: Specify the image to start with
-t n	: Specify a threshold value for point detection
-D	: Debugging mode.  Will output lots of graphs, messages, etc
-h	: This help message
"""

import Analysis
from multiprocessing import Manager, Pool, cpu_count, Value, Process
from multiprocessing.managers import SyncManager
from scipy.io import savemat
import pyfits
from glob import glob
import sys, re
from os import path
from time import time, sleep, strftime
import signal
reload(Analysis)

THRESH = 1500
DEBUG = False

NORMAL_FLAG = 0
STOP_FLAG = 1

def single_processor(filequeue, pointslist, donelist, bgimg = None, 
		basedir = None, thresh=THRESH):
	
	while not filequeue.empty():
		fname = filequeue.get()
		frame_num = int(path.splitext(path.split(fname)[-1])[0])

		
		if basedir:
			pass
			
			
		if len(donelist)%100 == 0:
			sys.stderr.write("Completed %d\n"%(len(donelist)))
			sys.stderr.write("Found %d holes\n" %
								len(pointslist))			
		
		try:
			img1, img2 = Analysis.loadsplit(fname, bgimg = bgimg)
			pointslist.extend(Analysis.findpairs(img1, img2, thresh=thresh, 
						DEBUG=DEBUG, abs_thresh=True, 
						frame_num = frame_num))
			donelist.append(fname)
		except IOError:
			pass
		except KeyboardInterrupt:
			return
		

def processor(args):
	"""map-able function that processes a single frame of data
	 
	Argument: a single tuple composed of the following, in order
	file_name : string, required
	pointslist : list, required
	file_number : ignored, optional
	background : array, optional
	donelist : list, optional
		A list of files that have already been processed
	status : ??????
	"""
	
	
	fname = args[0]
	frame_num = int(path.splitext(path.split(fname)[-1])[0])
	pointslist = args[1]
	if len(args) > 2: i = args[2]
	if len(args) > 3: 
		bgimg = args[3]
	else:
		bgimg = None
	if len(args) > 4:
		donelist = args[4]
		donelist.append(i)
		if len(donelist)%1000 == 1:
			sys.stderr.write("Completed %d\n"%(len(donelist)-1))
			sys.stderr.write("Found %d holes\n" % len(pointslist))
		if len(donelist)%10000 == 0 and len(pointslist) > 0:
			xl, yl, varxl, varyl, el, xr, yr, varxr, varyr, er, framenum =\
					zip(*list(pointslist))
			savemat('tempfile.mat', 
				{'xl':xl, 'yl':yl, 'varxl': varxl, 'xr':xr, 'yr':yr, 
				'el': el, 'er': er, 'varxr': varxr,  'framenum':framenum},
					oned_as = 'row')
			sys.stderr.write("Saved a snapshot\n")

	if len(args) > 5:
		THRESH = args[5]
			
	# Finally, load in the image
	try:
		img1, img2 = Analysis.loadsplit(fname, bgimg = bgimg)
	except IOError:
		print "Failed loading!"
		return
	pointslist.extend(Analysis.findpairs(img1, img2, thresh=THRESH, 
				DEBUG=DEBUG, abs_thresh=True, 
				frame_num = frame_num))
	#pointslist.append((0,0,0,0))
	


def user_input(val):
	"""docstring for user_input"""
	while True:
		sleep(1)
		interaction = sys.stdin.readline().strip()
		print "Received message from user '%s'" % interaction
		if interaction == "stop":
			val = STOP_FLAG
			return

def makebackground(filelist, n = 300):
	import numpy as np
	from random import randrange as rand
	
	filedesc = Analysis.imread(filelist[0])
	[r,c] = np.shape(filedesc)
	mat = np.empty((r,c,n))
	for i in range(n):
		mat[:,:,i] = Analysis.imread(filelist[rand(len(filelist))])
	return np.median(mat, axis=2)


def inthandler(signum, frame):
	val= STOP_FLAG
	print frame
	print signum
	print "Keyboard Interrupt should stop processes gracefully"


if __name__ == '__main__':
	import os
	import sys
	from getopt import getopt, GetoptError
	from optparse import OptionParser
	
	### Option Defaults ###
	parser = OptionParser(usage="Usage: %prog -d FILES")
	parser.set_defaults(multi=True, profile=False, queueing=False, 
			savefile=strftime('%m%d-map'), start=0, end=None, debug=0,
			thresh=5000, bgname=100, dirname='./*/*/*.tif')

	### Input/Output Options ###
	parser.add_option('-f', '--specification', dest='dirname',
			help='Glob pattern for files to process'
				' (e.g. G:\\Data\\Map\\*\\*)')
	parser.add_option('-o', '--output-file', dest='savefile',
			help='Output file (defaults to a date-specific form'
			      ', which is %default.mat today)')
	parser.add_option('-B', '--make-bg', dest='bgname',
			help="Make a background from NUM randomly selected images", 
			metavar="NUM", type="int")
	parser.add_option('-b', '--bgimg', dest='bgname', 
			help="Use BGNAME as the background image")

	### Parallel processing ###
	parser.add_option('-1', '--single-processor', dest='multi', 
			help="Use Single Processor logic", 
			action="store_false")
	parser.add_option('-m', '--multiprocessor', dest='multi', 
			help="Use Multiple Processors",
			action="store_true")
	parser.add_option('-q', '--queue', dest='queueing',
			help="Use Queueing logic (probably broken!)", 
			action="store_true")

	### Debugging-type options

	parser.add_option('-D', '--debug', dest='debug',
			help="Increase debug level (higher = more data)",
			action="count")
	parser.add_option('-p', '--profiling', dest='profile',
			help='Puts program in profiling mode'
			' (disables most plotting and waiting)',
			action='store_true')
	parser.add_option('-t', '--threshold', dest='thresh', type="int",
			help="Threshold for holes above the background")

	### Subsets of the image set ###
	parser.add_option('-s', '--start', dest='start', type='int',
			help="Start at the START-th frame")
	parser.add_option('-e', '--end', dest='end', type='int',
			help="End at the ENDth frame")
	def cutoff_callback(option, opt_str, value, parser):
		parser.values.end = parser.values.start + value
		#option.end = option.start + value
	parser.add_option('-c', '--cutoff', type="int", metavar="CUTOFF",
			help="Process a maximum of CUTOFF frames, starting with the"
			" START-th (which defaults to the first)", 
			action="callback", callback=cutoff_callback)


	(opts, args) = parser.parse_args()
	
	sys.stderr.write( "Setting up list\n")
	val = 0
	m = Manager()
	pointlist = m.list()
	donelist = m.list()
		
	sys.stderr.write( "Setting up Pool\n")
	p = Pool(processes=cpu_count()+2)
		

	print "Globbing on '%s'" % opts.dirname
	filelist = glob(opts.dirname)
	print "Globbed"
	fulllist = filelist
	filelist = filelist[opts.start:opts.end]
	
	n = len(filelist)
	sys.stderr.write("Found %d files\n" % n)
	
	if n == 0:
		print "Could not find any files! Quitting..."
		sys.exit(1)
	
	if isinstance(opts.bgname, str):
		bgimg = pyfits.open(opts.bgname)[0].data
	else:
		print "Making background image"
		bgimg = makebackground(fulllist, opts.bgname)
		print "Done making background image"
		hdu = pyfits.PrimaryHDU(bgimg)
		print "S1"
		hdulist = pyfits.HDUList([hdu])
		print "S2"
		if os.path.exists(opts.savefile+'.fits'):
                        os.renames(opts.savefile+'.fits', opts.savefile+'.fitsold')
		hdulist.writeto(opts.savefile+'.fits')
		
		if opts.debug > 0:
			from pylab import *
			imshow(bgimg)
			colorbar()

	try:
		print "Loaded background image"
		processes = []
		print r"Starting in 3 \a"
		sleep(1)
		print r"2 \a"
		sleep(1)
		print r"1 \a"
		sleep(1)
		print r"Go! \a\a"
		tic = time()
		if opts.queueing:
			q = m.Queue()
			for n in filelist:
				q.put(n)
			for n in range(cpu_count()):
				processes.append(Process(target=single_processor, 
					args=(q, pointlist, donelist, bgimg)))
				processes[n].start()
				sys.stderr.write("Starting process %d\n"%n)
			for n in range(cpu_count()):
				processes[n].join()
		else:
			if opts.multi:
				res = p.map(processor, zip(filelist, [pointlist]*n, 
							range(n), [bgimg]*n, [donelist]*n, [opts.thresh]*n))
			else:
				res = map(processor, zip(filelist, [pointlist]*n, range(n), 
							[bgimg]*n, [donelist]*n, [opts.thresh]*n))
	except KeyboardInterrupt:
		print "BALLS!"
		from pylab import show
		show()
	except MemoryError:
		pointlist = list(pointlist)[0:-50]
		print "Memory Error! Only made it as far as %d" % len(donelist)
	finally:
		print "For %d frames, found %d spots, in %f seconds (%f fps)" % \
		      (len(filelist), len(pointlist), time() - tic, 
			  (len(filelist))/(time() - tic + 1e-10))
		if len(pointlist) != 0:
			xl, yl, varxl, varyl, el, xr, yr, varxr, varyr, er, framenum = zip(*list(pointlist))
			
			savemat(opts.savefile, 
				{'xl':xl, 'yl':yl, 'xr':xr, 'yr':yr, 
				'el': el, 'er': er, 'framenum':framenum, 'varxr' : varxr, 
				'varyr' : varyr, 'varxl': varxl, 'varyl' : varyl},
				oned_as = 'row')
			if not opts.profile:
				from pylab import *
		
				figure()
				plot(xl, yl, 'bx')
				figure()
				plot(xr, yr, 'ro')
				show()
		
	
	
	
	
