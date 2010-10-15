import Analysis, os, math

from optparse import OptionParser
from glob import glob
from numpy import array, median, mean,  sqrt, floor
from scipy import io

from pylab import plot, quiver, title, quiverkey, figure

if __name__ == "__main__":
	parser = OptionParser(usage = "Usage: %prog [opts] args")
	
	# Either we use a mapping file 
	parser.add_option('-m', '--map', dest = "map", 
				help = "Mapping file base name ", default = False)
	parser.add_option('-2', '--2nd-map', dest = "map2", 
				help = "Second round map", default = False)
	parser.add_option('-s', '--save-offsets', dest="save_map2",
				action="store_true", default = False,
				help = "Save the offset map for later use")
	# Or we enter the translation manually
	parser.add_option('--x-shift', dest = "xshift",
				help = "Shift in x between the two channels", default = 0, 
				type="float")
	parser.add_option('-y', '--y-shift', dest = "yshift",
				help = "Shift in y between the two channels (default 256 px)", 
				default = 256, type="float")
	# Or we have a single point-pair that should match up, and calculate 
	#  translation from that
	parser.add_option('--x1', dest = "x1", default = 0, type = "float")
	parser.add_option('--x2', dest = "x2", default = 0, type = "float")
	parser.add_option('--y1', dest = "y1", default = 0, type = "float")
	parser.add_option('--y2', dest = "y2", default = 0, type = "float")
	
	parser.add_option('-x', '--pixel-size', dest = "pxsize",
				help =  "Pixel size (default 106.6)", default = 106.667, 
				type = "float")
	parser.add_option('-r', '--max-r', dest = "max_r",
				help = "Maximum allowed inter-color colocalization distance",
				default = 100, type = "float")
	parser.add_option('-q', '--quiet', dest = "quiet", 
				action = "store_true", default = False)
	parser.add_option('-d', '--quiver-distance', dest="quiv_dist", 
				help = "Minimum distance between points on the quiver map",
				default = 10)
	opts, args = parser.parse_args()
	
	
	if not opts.map:
		if opts.x1 and opts.x2 and opts.y1 and opts.y2:
			opts.xshift = opts.x2 - opts.x1
			opts.yshift = opts.y2 - opts.y1
	else:
		mapping = Analysis.loadmapping(opts.map)
	
	if opts.map2:
		mapping2 = Analysis.loadmapping(opts.map2)
	
	if len(args) == 1 and '*' in args[0]:
		args = glob(args[0])
	
	print "Found this many files", len(args)
	xrs = []
	xls = []
	yrs = []
	yls = []
	varxrs = []
	varxls = []
	for fname in args:
		try:
			MLData = io.loadmat(fname, squeeze_me = True)
			for var in ('xl', 'xr', 'yl', 'yr', 'varxr', 'varxl'):
				exec "%ss.extend(MLData['%s'])" % (var, var)
		except:
			print "Failed on file", fname, "for some reason..."
	
	xls = array(xls)
	yls = array(yls)
	xrs = array(xrs)
	yrs = array(yrs)
	
	goodxs = []
	goodys = []
	keepxs = []
	keepys = []
	diffxs = []
	diffys = []
	
	if opts.map:
		xns, yns = mapping(xrs, yrs)
	else:
		xns = xrs + opts.xshift
		yns = yrs + opts.yshift
		

	bestd2s = (xns - xls)**2 + (yns - yls)**2
	
	sel = bestd2s*opts.pxsize**2 < opts.max_r**2
	
	goodxs = xns[sel]
	goodys = yns[sel]
	diffxs = (xls - xns)[sel] * opts.pxsize
	diffys = (yls - yns)[sel] * opts.pxsize

	print "Colocalized ", len(goodxs), " spots at an average error of ", 
	print mean(sqrt(diffxs**2 + diffys**2)) 
	
	if opts.map2:
		xds, yds = mapping2(goodxs, goodys)
		goodxs += xds/opts.pxsize
		goodys += yds/opts.pxsize
		diffxs = (xls[sel] - goodxs) * opts.pxsize
		diffys = (yls[sel] - goodys) * opts.pxsize
	
		print "In the second round, those colocalized at an error of",
		print mean(sqrt(diffxs**2 + diffys**2)) 
	else:
		if opts.save_map2 \
			or raw_input('Save Second Pass? y/[n]').lower()[0] == 'y':
			Analysis.makeLSQspline(diffxs, diffys, goodxs, goodys, 
									savefile= 'offsets'+os.path.basename(fname),
									n = floor(max(2,sqrt(len(goodys)/10))))
	if len(goodxs):
		goodxf = [goodxs[0]]
		goodyf = [goodys[0]]
		diffxf = [diffxs[0]]
		diffyf = [diffys[0]]
		
		
		print "Selecting low density..."
		
		for goodx, goody, diffx, diffy in zip(goodxs, goodys, diffxs, diffys):
			if min(sqrt((goodx - array(goodxf))**2 + (goody - array(goodyf))**2)) > opts.quiv_dist:
				goodxf.append(goodx)
				goodyf.append(goody)
				diffxf.append(diffx)
				diffyf.append(diffy)
	
		if not opts.quiet:
			figure()
			Q = quiver(goodxf, goodyf, diffxf, diffyf, 
						angles='xy', minshaft=2, units='dots', scale=1)
			scale = math.sqrt(median(array(diffx)**2 + array(diffy)**2)) 
			title('%s with mapping %s and error < %d' % 
						(os.path.dirname(fname) ,
						 str(opts.map or opts.yshift), 
						 opts.max_r))
			print scale
			if scale < 50:
				quiverkey(Q, .1, .1, 10, '$10 nm$', color="blue")
			else:
				quiverkey(Q, .1, .1, 1000, r'$1\mu m$', color="blue")
			figure()
			plot(diffxs, diffys, 'ro')
			title(os.path.dirname(fname))

