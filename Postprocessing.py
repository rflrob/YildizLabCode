#!/Library/Frameworks/Python.framework/Versions/5.1.0/bin/python

import sys
from scipy.io import loadmat, savemat
import Analysis
from numpy import sqrt, zeros, round, ceil, shape, array, median, arange, mean
from numpy.random import rand
from os.path import basename
from getopt import getopt
from optparse import OptionParser

#
#
# Generally, this program has  major phases
# * Read in all the command line options
#     (see the optparse module in the Python docs)
# * Get rid of data based on various criteria (specified by options)
# * Make the spline (just one line, actually)
# * See if the spline is any good, and output data 
n = 20


########################### Parsing ###################################

parser = OptionParser(usage='Usage: %prog [options] data.mat')
parser.set_defaults(n=20, plot=True, stepsize=1, interact=False, 
		multi=False, trim_edge=True, fraction=[1.0], memclear=False)
parser.add_option('-n', '--num-gridsquares', dest="n", type="int",
		help="Number of grid squares for making the map")
#Plotting flags
parser.add_option('-p', '--plot', dest='plot', action="store_true",
		help="Plot results of map making")
parser.add_option('-q', '--quiet', dest='plot', action="store_false",
		help="Suppress plotting")
#Parallel processing flags
parser.add_option('-m', '--multi-processor', dest="multi",
		action="store_true",
		help="Use multiple processors for making map (unstable on windows)")
parser.add_option('-1', '--single-processor', dest="multi",
		action="store_false",
		help="Force single-processor for map making")

#Data trimming options
parser.add_option('-s', '--step', dest="stepsize", type="int",
		help="Keep only every Ith spot", metavar="I")
parser.add_option('-F', '--full-screen', dest="trim_edge", 
		action="store_false", 
		help="Do not trim the outermost edge of the frames")

def fractioner_callback(option, opt_str, value, parser):
	print option
	print opt_str
	print value
	print parser
	if value.count(':'):
		start, step, stop = map(float, value.split(':'))
		parser.values.fraction = arange(start, stop, step)
	else:
		parser.values.fraction = array([float(value)])
parser.add_option('-f', '--fraction', dest="fraction",type="string", 
		help="Keep only the given fraction of the data (can accept" 
			" multiple values using slice notation)",
		action="callback", callback=fractioner_callback)

#Other options

parser.add_option('-i', '--interactive', dest="interact", action="store_true",
		help="Drop into interactive mode at key points")
parser.add_option('-M', '--conserve-memory', dest="memclear", action="store_true",
		help="Be ultraconservative with memory")
opts, args = parser.parse_args()

for frac in opts.fraction: 
	STEPSIZE = int(10/frac)
	print "-"*72
	print "Keeping %f%% of the data "%(100*frac)
	for filename in args:
		# Pull out the base name for saving output
		fname = ''.join(basename(filename).split('.')[:-1])
		#print "Loading data"
	
		D = loadmat(filename, squeeze_me = True, 
				struct_as_record=True)


		xld = D['xl']; yld = D['yl']
		xrd = D['xr']; yrd = D['yr']
		varl = D['varxl']; varr = D['varxr']
		del D

################################ Filter the Data ######################	
		
		# Get rid of anything where the width of the fit is too far 
		# outside of norms
		varllo, varlhi = Analysis.middle_percent(abs(varl), .02)
		varrlo, varrhi = Analysis.middle_percent(abs(varr), .02)
		print "Variance tolerance left:", varllo, varlhi
		print "Variance tolerance right:", varrlo, varrhi
		var_sel = ((varllo <= abs(varl)) * (abs(varl) <= varlhi) 
				* (varrlo <= abs(varr)) * (abs(varr) <= varrhi))

		stepper = rand(len(xld)) < frac
		
		if opts.trim_edge:  # Trim the outside border (where points are less reliable)
			xlo, xhi = Analysis.middle_percent(xld, .02)
			ylo, yhi = Analysis.middle_percent(yld, .02)
			selA = ((xlo < xld) * (xld < xhi) 
					*  (ylo < yld) * (yld < yhi))
			
			# Get rid of anything where the match isn't actually that good.
			xdiff = median(xld - xrd)
			ydiff = median(yld - yrd)
			selB = ((abs(xld - xrd - xdiff) < 5) 
					* (abs(yld - yrd - ydiff) < 5))
			print "Target displacement", xdiff, ydiff
			
			print "Rejecting %d based on variances, " \
				"%d based on displacements" % \
				(len(selA) - sum(selA), len(selB) - sum(selB))

			# sel is the variable used to actually pull out the good values
			sel = var_sel * selA * selB * stepper
		else:
			sel = var_sel * stepper
		
		if opts.memclear:
			print "Clearing variables"
			del varllo, varlhi, varl, varrlo, varrhi, 
			del stepper, xlo, xhi, ylo, yhi
			xl = xld[sel]
			del xld
			yl = yld[sel]
			del yld
			xr = xrd[sel]
			del xrd
			yr = yrd[sel]
			del yrd, sel
		else:		
			xl = xld[sel]; yl = yld[sel]; xr = xrd[sel]; yr = yrd[sel];

		if opts.interact: 
			from IPython.Shell import IPShellEmbed
			ipshell = IPShellEmbed([], banner='\a\a\aEntering Interpreter')
			print '\a\a\a'
			ipshell()

##############################  Make the Spline #######################
#		print "Splining!"
		mapping = Analysis.makeLSQspline(xl, yl, xr, yr, n = opts.n, 
				savefile = fname+'_1', multi=opts.multi)


##############################  Evaluate spline quality ###############
#		print "applying on all good data"
		xn, yn = mapping(xrd[sel], yrd[sel])
		diffx = xld[sel] - xn
		diffy = yld[sel] - yn
		diffmag = sqrt(diffx**2 + diffy**2)
		diffmags = sorted(diffmag)
		print "Median: ", median(diffmag), \
			"1%", diffmags[int(.01*len(diffmags))], \
			"5%", diffmags[int(.05*len(diffmags))], \
			"10%", diffmags[int(.10*len(diffmags))], \
			"20%", diffmags[int(.20*len(diffmags))], \
			"30%", diffmags[int(.30*len(diffmags))], \
			"40%", diffmags[int(.40*len(diffmags))], \
			"60%", diffmags[int(.60*len(diffmags))], \
			"70%", diffmags[int(.70*len(diffmags))], \
			"80%", diffmags[int(.80*len(diffmags))], \
			"90%", diffmags[int(.90*len(diffmags))], \
			"95%", diffmags[int(.95*len(diffmags))], \
			"99%", diffmags[int(.99*len(diffmags))]

		if opts.plot:
	#		print "applying spline"
			xn, yn = mapping(xr, yr)
			diffx = xl - xn
			diffy = yl - yn
			diffmag = sqrt(diffx**2 + diffy**2)
			diffs = zeros((ceil(yr.max())+2, ceil(xr.max())+2))
			ns = zeros(shape(diffs))
			

			diffs += 1e-10


	#		print "Making error plot"
			for c, r, e in zip(xr, yr, diffmag):
				c = round(c)
				r = round(r)
				diffs[r,c] += e
				ns[r,c] += 1

			print "ns are in the range", ns[10:-10, 10:-10].min(), \
					ns[10:-10, 10:-10].mean(), ns[10:-10, 10:-10].max()
			
			print "ns per gridsquare are in the range"
			from pylab import contourf, colorbar, title, figure, ion
			ion()
			figure()
			contourf(ns)
			colorbar()
			figure()
			contourf((diffs*106/ns).clip(0,8))
			colorbar()
			title('Average Errors')

			savemat('%s_diffs_step%d_n%d' % (fname, STEPSIZE, n) , 
					{'diffs' : diffs, 'ns': ns, 'diffmag': diffmag})



		if opts.interact:
			from pylab import *
			print '\a\a\a'
			ipshell() 
