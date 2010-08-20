import Mapping
from optparse import OptionParser
from os import path
from numpy import array

parser = OptionParser(usage='Usage: %prog [opts] 585FILE [655FILE]')

parser.add_option('-x', '--pixel-size', dest='pxsize', type="float",
		help="Pixel Size (default 106.667 nm/px)", default=106.667)

parser.add_option('-H', '--hole-map', dest="holemap",
		help="Output of PostProcessing.py")
parser.add_option('-B', '--bead-map', dest="beadmap",
		help="Output of CombineWHSpots.py (offsets...)")

parser.add_option('-p', '--in-pixels', dest="in_nm", action="store_false",
		help="Use this if dynein traces have been converted to pixels",
		default=True)

opts, args = parser.parse_args()

file585 = args[0]
if len(args) > 1:
	file655 = args[1]
else:
	file655 = False

mapping = Mapping.loadmapping(opts.holemap)
mapping2 = Mapping.loadmapping(opts.beadmap)


x585, y585 = array(zip(*[(float(line.split()[0]), float(line.split()[1])) 
	for line in file(file585) 
		if line[0].isdigit()]))

if file655:
	x655, y655 = array(zip(*[(float(line.split()[0]), float(line.split()[1])) 
		for line in file(file655) 
			if line[0].isdigit()]))
else:
	x655, y655 = (zeros(len(x585)), zeros(len(585)))

if opts.in_nm:
	x655 /= opts.pxsize
	y655 /= opts.pxsize
	x585 /= opts.pxsize
	y585 /= opts.pxsize

x585m, y585m = mapping(x585, y585) 
xd, yd = mapping2(x585m, y585m)


x585m += xd/opts.pxsize
y585m += yd/opts.pxsize


dirname,fname = path.split(file585)
fname = 'Remapped_' + fname
print "Outputting to ", path.join(dirname, fname)
outfile = open(path.join(dirname, fname), 'w')
for x, y in zip(x585m, y585m):
	outfile.write('%f\t%f\n' % (x*opts.pxsize, y*opts.pxsize))


outfile.close()
 

