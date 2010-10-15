#/usr/bin/python


from scipy import io
from optparse import OptionParser

if __name__ == "__main__":
	parser = OptionParser(usage="Usage: %prog inputfile.mat outputfile.xml")
	
	opts, args = parser.parse_args()
	assert len(args) == 2
	
	Data = io.loadmat(args[0], squeeze_me = True)
	imgname = Data['imgname']
	
	framesets = zip(Data["tpmins"], Data["tpmaxes"]+1)
	plotpoints = []
	if 'xl_fids' in Data:
		plotpoints.append((Data['xl_fids'], Data['yl_fids'], Data['framesetnum_fids']))
		plotpoints.append((Data['xr_fids'], Data['yr_fids'], Data['framesetnum_fids']))
		plotpoints.append((Data['xl_exp'], Data['yl_exp'], Data['framesetnum_exp']))
		plotpoints.append((Data['xr_exp'], Data['yr_exp'], Data['framesetnum_exp']))
	else:
		plotpoints.append((Data['xl'], Data['yl'], Data['framesetnum']))
		plotpoints.append((Data['xr'], Data['yr'], Data['framesetnum']))
	
	
	plotpoints.append((Data['DQ_varbig_x'], Data['DQ_varbig_y'], Data['DQ_varbig_t']))
	plotpoints.append((Data['DQ_nomatch_x'], Data['DQ_nomatch_y'], Data['DQ_nomatch_t']))
	
	outfile = open(args[1], 'w')
	outfile.write('<?xml version="1.0" encoding="UTF-8"?>\n')
	outfile.write("<CellCounter_Marker_File>\n")
	outfile.write("<Image_Properties>\n"
     "\t<Image_Filename>%s</Image_Filename>\n"
 	"</Image_Properties>\n" % imgname)

	outfile.write('<Marker_Data>\n')
	outfile.write('\t<Current_Type>1</Current_Type>\n')
	

	
	marker_type = 1
	for xs, ys, fsnums in plotpoints:
		outfile.write('\t<Marker_Type> \n')
		outfile.write('\t\t<Type>%d</Type>\n' % marker_type)
		for x, y, fsnum in zip(xs, ys, fsnums):
			for fnum in range(*map(int,framesets[int(fsnum)])): 
				outfile.write('\t\t<Marker><MarkerX>%d</MarkerX> '
									'<MarkerY>%d</MarkerY> '
									'<MarkerZ>%d</MarkerZ> '
									'</Marker>\n' % (int(x), int(y), int(fnum)))
		outfile.write('\t</Marker_Type>\n')
		marker_type += 1
	print "Almost", 
	outfile.write('</Marker_Data>\n')
	
	outfile.write("</CellCounter_Marker_File>\n")
	outfile.close()
	print "There!"
	