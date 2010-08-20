from glob import glob
from optparse import OptionParser
from re import findall
from xml.dom import minidom
from collections import defaultdict
import os


def getElementData(element, tagname):
	return element.getElementsByTagName(tagname)[0].firstChild.data

def getAllData(element, tagname):
	children = element.getElementsByTagName(tagname)
	return [child.firstChild.data for child in children]

def getFrameSets(tree):
	types = tree.getElementsByTagName('Type')
	for type in types:
		if type.childNodes[0].data == "3":
			framesets = []
			framenums = map(int, getAllData(type.parentNode, 'MarkerZ'))
			framenums.sort()
			lastframe = -1
			startframe = -1
			for frame in framenums:
				if frame != lastframe + 1 and frame != lastframe:
					if lastframe > 0:
						framesets.append((startframe, lastframe))
					startframe = frame
				lastframe = frame
			if lastframe > 0:
				framesets.append((startframe, lastframe))
			return framesets

def getFrameSetNum(framesets, frame):
	for i in xrange(len(framesets)):
		if framesets[i][0] <= frame <= framesets[i][1]:
			return i
	print "Could not find frame number", frame

if __name__ == "__main__":
		parser = OptionParser(usage="usage: %prog fileglob")
		(options, args) = parser.parse_args()

		flagdict = defaultdict((lambda : 'ERR'), {'1': '655', '2':'585'})
		outfile = None
		framesets = []
		markernums = defaultdict(int)
		print glob(args[0] + '*')
		filenum = 0
		for fname in glob(args[0] + '*'):
			XMLTree = minidom.parse(fname)
			

			# Read out frame numbers from the file name
			if 'frame' in fname:
				frames = fname.split('frame')[1].rsplit('.xml')[0]
				startframe, endframe = map(int, frames.split('-'))
				framesets.append((startframe, endframe))
			else:
				framenums = map(int, getAllData(XMLTree, 'MarkerZ'))
				startframe = min(framenums)
				endframe = max(framenums)
				framesets = getFrameSets(XMLTree)
			print fname, framesets


			for node in XMLTree.childNodes:
				# Ignore if not the right kind of element
				if node.nodeName != "CellCounter_Marker_File":
					continue

				# Setup header if we haven't already
				if not outfile:
					namenode = node.getElementsByTagName('Image_Filename')[0]
					imagename = getElementData(node, 'Image_Filename')
					print imagename
					outname = os.path.splitext(imagename)[0]+ '_spotlist.txt'
#					outname = outname.replace('.fits', '_spotlist.txt')
					outname = os.path.join(os.path.dirname(fname), outname)
					print outname
					outfile = open(outname, 'w')

					outfile.write('FileName=%s;\n\n'%imagename)	
					outfile.write('Sx\tSy\tStart\tEnd\tFlag\tPeak\n')


				types = node.getElementsByTagName('Type')
				for typenode in types:
					flag = flagdict[typenode.firstChild.data]
					if flag == "ERR":
						continue
					markernum = 0
					for marker in \
						typenode.parentNode.getElementsByTagName('Marker'):
						xpos = getElementData(marker, 'MarkerX')
						ypos = getElementData(marker, 'MarkerY')
						framenum = int(getElementData(marker, 'MarkerZ'))
						
						filenum = getFrameSetNum(framesets, framenum)
						markernum = markernums[filenum]

						outfile.write('%s\t%s\t%d\t%d\t%s\t%d\n' %
									(xpos, ypos, framesets[filenum][0], 
									 framesets[filenum][1], flag, 
									 100*filenum + markernum))
						markernums[filenum] += 1



			filenum += 1
		outfile.close()
