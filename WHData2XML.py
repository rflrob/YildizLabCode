#/usr/bin/python


from scipy import io
from optparse import OptionParser
from os.path import basename
from functools import reduce

if __name__ == "__main__":
    parser = OptionParser(usage="Usage: %prog inputfile.mat outputfile.xml")
    parser.add_option('-s', '--spotlist', dest="spotlist", default=None)

    opts, args = parser.parse_args()
    assert len(args) == 2
    
    Data = io.loadmat(args[0])
    imgname = Data['imgname'][0]

    
    
    if Data['framebyframe']:
        framesets = zip([range(max(Data["tpmaxes"])),
                        range(max(Data["tpmaxes"])+1)])
    else:
        framesets = zip(Data["tpmins"], Data["tpmaxes"]+1)
    plotpoints = []
    if 'xl_fids' in Data:
        plotpoints.append((Data['xl_fids'], Data['yl_fids'],
            Data['framesetnum_fids']))
        print "Type %d: Fiducials in 655" % len(plotpoints)
        plotpoints.append((Data['xr_fids'], Data['yr_fids'], 
            Data['framesetnum_fids']))
        print "Type %d: Fiducials in 585" % len(plotpoints)
        plotpoints.append((Data['xl_exp'], Data['yl_exp'], 
            Data['framesetnum_exp']))
        print "Type %d: Test points in 655" % len(plotpoints)
        plotpoints.append((Data['xr_exp'], Data['yr_exp'], 
            Data['framesetnum_exp']))
        print "Type %d: Test points in 585" % len(plotpoints)
    else:
        plotpoints.append((Data['xl'], Data['yl'], Data['framesetnum']))
        print "Type %d: Matched points in 655" % len(plotpoints)
        plotpoints.append((Data['xr'], Data['yr'], Data['framesetnum']))
        print "Type %d: Matched points in 585" % len(plotpoints)
    
    plotpoints.append((Data['DQ_varbig_x'], Data['DQ_varbig_y'], 
        Data['DQ_varbig_t']))
    print "Type %d: Point not stable enough" % len(plotpoints)
    plotpoints.append((Data['DQ_nomatch_x'], Data['DQ_nomatch_y'], 
        Data['DQ_nomatch_t']))  
    print "Type %d: Did not find a good match" % len(plotpoints)
    
    if opts.spotlist:
        flags = set([line.split()[4] for line in open(opts.spotlist) if
                line[0].isdigit()])
        for flag in flags:
            sx, sy, fstart, fend = zip(*[map(int, 
                [line.split()[0], line.split()[1], line.split()[2],
                    line.split()[3]])
                for line in open(opts.spotlist)
                if line[0].isdigit() and line.split()[4] == flag])
            comb = lambda x,y: x+y
            plotpoints.append((
                reduce(comb, [[x]*(fe - fs +1) 
                    for x, fs, fe in zip(sx, fstart, fend)]),
                reduce(comb, [[y]*(fe - fs +1) 
                    for y, fs, fe in zip(sy, fstart, fend)]),
                reduce(comb, [range(fs, fe+1) 
                    for fs, fe in zip(fstart, fend)])))
            print "Type %d: Original spotlist locs for %s" \
                    %(len(plotpoints), flag)

    outfile = open(args[1], 'w')
    outfile.write('<?xml version="1.0" encoding="UTF-8"?>\n')
    outfile.write("<CellCounter_Marker_File>\n")
    outfile.write("<Image_Properties>\n"
     "\t<Image_Filename>%s</Image_Filename>\n"
    "</Image_Properties>\n" % basename(imgname))

    outfile.write('<Marker_Data>\n')
    outfile.write('\t<Current_Type>1</Current_Type>\n')
    

    
    marker_type = 1
    for xs, ys, fsnums in plotpoints:
        outfile.write('\t<Marker_Type> \n')
        outfile.write('\t\t<Type>%d</Type>\n' % marker_type)
        for x, y, fsnum in zip(xs, ys, fsnums):
            if Data['framebyframe']:
                outfile.write('\t\t<Marker><MarkerX>%d</MarkerX> '
                    '<MarkerY>%d</MarkerY> '
                    '<MarkerZ>%d</MarkerZ> '
                    '</Marker>\n' % (int(x), int(y), int(fsnum)))

            else:
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
    
