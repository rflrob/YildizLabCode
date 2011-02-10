from glob import glob
from optparse import OptionParser
from re import findall
from xml.dom import minidom
from collections import defaultdict
import os, math


def getElementData(element, tagname):
    return element.getElementsByTagName(tagname)[0].firstChild.data

def getAllData(element, tagname):
    children = element.getElementsByTagName(tagname)
    return [child.firstChild.data for child in children]

def getFrameSets(tree, colors=1.0):
    types = tree.getElementsByTagName('Type')
    framesets = []
    #for type in types:
    #    if type.childNodes[0].data == "3" or True:
    framenums = map(int, getAllData(tree, 'MarkerZ'))
    framenums.sort()
    lastframe = -10
    startframe = -10
    for frame in framenums:
        frame = int(math.ceil(frame/colors))
        if not lastframe <= frame <= lastframe + 2:
            # Assume if it's missing one, that's a mistake, otherwise,
            # change the above to  ... <= lastframe + 1:
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
        parser.add_option('-x', dest='xoffset', type='float', default=False,
                help="Calculate lower channel offset by x")
        parser.add_option('-y', dest='yoffset', type='float', default=False,
                help="Calculate lower channel offset by y")
        parser.add_option('-c', dest='color', action='store_const', const=2.0,
                default=1.0, help="Use output from a two-color stack")
        parser.add_option('-g', dest='color', action='store_const', const=1.0,
                default=1.0, help="Guessing positions of other half of channel"
                "(but not in a two-color way)")
        parser.add_option('-m', dest='map', default=False,
                help="Input the map to estimate positions")
        parser.add_option('-o', dest='other', default='655')
        (opts, args) = parser.parse_args()

        flagdict = defaultdict((lambda : 'ERR'), {'1': '655', '2':'585'})
        outfile = None
        framesets = []
        markernums = defaultdict(int)
        print glob(args[0] + '*')
        filenum = 0
        
        if opts.map is not False:
            import Mapping
            mapping = Mapping.loadmapping(opts.map)

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
                framesets = getFrameSets(XMLTree, opts.color)
            print fname, framesets


            for node in XMLTree.childNodes:
                # Ignore if not the right kind of element
                if node.nodeName != "CellCounter_Marker_File":
                    continue

                # Setup header if we haven't already
                if not outfile:
                    namenode = node.getElementsByTagName('Image_Filename')[0]
                    imagename = getElementData(node, 'Image_Filename')
                    imagename2 = fname.split('.')[0]+'.tif'
                    print imagename, imagename2
                    if '.tif' not in imagename: imagename = imagename2
                    outname = os.path.splitext(imagename)[0]+ '_spotlist.txt'
#                   outname = outname.replace('.fits', '_spotlist.txt')
                    outname = os.path.join(os.path.dirname(fname), outname)
                    print outname
                    outfile = open(outname, 'w')

                    outfile.write('FileName=%s;\n\n'%imagename) 
                    outfile.write('Sx\tSy\tStart\tEnd\tFlag\tPeak\n')


                types = node.getElementsByTagName('Type')
                for typenode in types:
                    flag = flagdict[typenode.firstChild.data]
                    positions = defaultdict(list)
                    if flag == "ERR":
                        continue
                    markernum = 0
                    for marker in \
                        typenode.parentNode.getElementsByTagName('Marker'):
                            
                        xpos = int(getElementData(marker, 'MarkerX'))
                        ypos = int(getElementData(marker, 'MarkerY'))
                        framenum = int(math.ceil(
                            int(getElementData(marker, 'MarkerZ')) / opts.color))
                        
                        filenum = getFrameSetNum(framesets, framenum)

                        skip = False
                        for x,y in positions[filenum]:
                            if (xpos - x)**2 + (ypos - y)**2 < 5**2:
                                skip = True
                                break
                        else:
                            positions[filenum].append((xpos,ypos))
                            markernum = markernums[filenum]

                            outfile.write('%s\t%s\t%d\t%d\t%s\t%d\n' %
                                        (xpos, ypos, framesets[filenum][0], 
                                         framesets[filenum][1], flag, 
                                         100*filenum + markernum))
                            markernums[filenum] += 1
                            if (opts.xoffset is not False) \
                                    and (opts.yoffset is not False): 
                                outfile.write('%d\t%d\t%d\t%d\t%s\t%d\n' %
                                        (xpos + opts.xoffset, ypos + opts.yoffset, 
                                            framesets[filenum][0], 
                                            framesets[filenum][1], opts.other, 
                                            100*filenum + markernum+1))
                                markernums[filenum] += 1
                            elif opts.map is not False:
                                newx, newy = mapping(xpos, ypos)
                                outfile.write('%d\t%d\t%d\t%d\t%s\t%d\n' %
                                        (round(newx), round(newy), 
                                            framesets[filenum][0],
                                            framesets[filenum][1], opts.other,
                                            100*filenum + markernum + 1))
                                markernums[filenum] += 1





            filenum += 1
        outfile.close()
