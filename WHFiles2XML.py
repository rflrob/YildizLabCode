#/usr/bin/python

import os, re, sys
from os import path
from glob import glob
from scipy import io
from optparse import OptionParser

def write_markerdata(fname, pxsize = 106.667, outfile = sys.stdout):
	lineno = 1
	for line in file(fname):
		if line[0].isdigit():
			data = map(float, line.split())
			x = data[0]/pxsize
			y = data[1]/pxsize
			outfile.write('\t\t<Marker><MarkerX>%d</MarkerX> '
								'<MarkerY>%d</MarkerY> '
								'<MarkerZ>%d</MarkerZ> '
								'</Marker>\n' % (x,y, int(lineno)))
		elif 'x\t y' in line:
			lineno = 0			
		lineno += 1


#def main():
if __name__ == "__main__":
	parser = OptionParser(usage="Usage: %prog foldername outputfile.xml")
	parser.add_option('-x', '--pixel-size', type="float", dest="pxsize",
			help="Size of pixels, in nanometers", default=106.667)
	opts, args = parser.parse_args()
	assert len(args) == 2
	
	fnames = glob(path.join(args[0], '*'))
	outfile = open(args[1], 'w')

	imgname = path.basename(re.findall('(.*)_spot', fnames[0])[0] + '.tif')

    ## Write XML Header stuff
	outfile.write('<?xml version="1.0" encoding="UTF-8"?>\n')
	outfile.write("<CellCounter_Marker_File>\n")
	outfile.write("<Image_Properties>\n"
	 "\t<Image_Filename>%s</Image_Filename>\n"
	"</Image_Properties>\n" % imgname)
	outfile.write('<Marker_Data>\n')
	outfile.write('\t<Current_Type>1</Current_Type>\n')
	

	colorfinder = re.compile(r'spot\d*_(.*)_xy')
	colors = set([colorfinder.findall(fname)[0] for fname in fnames]) 

	for color_type, color in enumerate(colors):
		outfile.write('\t<Marker_Type> \n')
		outfile.write('\t\t<Type>%d</Type>\n' % (color_type + 1))
		for fname in fnames:
		    if color in colorfinder.findall(fname):
				write_markerdata(fname, opts.pxsize, outfile)

		outfile.write('\t</Marker_Type>\n')
	outfile.write('</Marker_Data>\n')
	outfile.write('</CellCounter_Marker_File>\n')
	outfile.close()

	



if __name__ == "__main__":
	pass#main()
