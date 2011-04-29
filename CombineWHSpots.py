#!/Library/Frameworks/Python.framework/Versions/5.1.0/bin/python

import Analysis, re, os, math

from optparse import OptionParser
from collections import defaultdict
from glob import glob
from numpy import array, std, mean, median, Inf, sqrt, diff
from scipy import io, rand

from pylab import plot, quiver, title, quiverkey, figure, ion
from __builtin__ import dir

reload(Analysis)

def gen_plotter(fnames):
        for fname in fnames:
                xs, ys, ns = list(zip(
                        *(list(map(float, 
                            (line.split()[0], line.split()[1], 
                                line.split()[-1])) )
                    for line in file(fname) if line[0].isdigit())) )
                yield (mean(ns), 
                        sqrt(mean(diff(xs)**2 + diff(ys)**2))/sqrt(2))


if __name__ == "__main__":
    parser = OptionParser(usage = "Usage: %prog [opts] files")
    
    # Either we use a mapping file 
    parser.add_option('-m', '--map', dest = "map", 
                help = "Mapping file base name ", default = False)
    parser.add_option('-2', '--2nd-map', dest = "map2", 
                help = "Second round map", default = False)
    parser.add_option('-S', '--save-offsets', dest="save_map2",
                action="store_true", default = False,
                help = "Save the offset map for later use")
    parser.add_option('-i', '--intra-frame-map', dest="frame_map",
                default = 0, type="float",
                help = "Calculate an offset map using some fraction of the "
                "points in the frame")
                
    # Or we enter the translation manually
    parser.add_option('--x-shift', dest = "xshift",
                help = "Shift in x between the two channels", default = 0, 
                type="float")
    parser.add_option('-y', '--y-shift', dest = "yshift",
                help = "Shift in y between the two channels (default 256 px)", 
                default = 256, type="float")
    # Or we have a single point-pair that should match up, and calculate translation from that
    parser.add_option('--x1', dest = "x1", default = 0, type = "float")
    parser.add_option('--x2', dest = "x2", default = 0, type = "float")
    parser.add_option('--y1', dest = "y1", default = 0, type = "float")
    parser.add_option('--y2', dest = "y2", default = 0, type = "float")
    
    parser.add_option('-F', '--frame-by-frame', dest="framewise", default=False, 
            help = "Process data from each frame separately", action="store_true")

    parser.add_option('--flip-y', dest="flip",
                help = "Flip the y axis", action="store_true", default = False)
    
    parser.add_option('-f', '--from-channel', dest = "from_chan",
                help = "Channel to map from (default 585)", default = "585")
    parser.add_option('-t', '--to-channel', dest = "to_chan",
                help = "Channel to map onto (default 655)", default = "655")
    parser.add_option('-x', '--pixel-size', dest = "pxsize",
                help =  "Pixel size (default 106.6)", default = 106.667, 
                type = "float")
    parser.add_option('-s', '--spot-std', dest = "max_std",
                help = "Maximum allowed inter-frame std dev (default 50)",
                default = 50, type="float")
    parser.add_option('-b', '--min-brightness', default=8000, type=float,
                help = "Minimum brightness for each spot")
    parser.add_option('-r', '--max-r', dest = "max_r",
                help = "Maximum allowed inter-color colocalization distance",
                default = 100, type = "float")
    parser.add_option('-R', '--max-2ndround-r', dest="max_R",
                default = 20, type="float",
                help = "Maximum allowed inter-color colocalization distance "
                        "in the 2nd round")
    parser.add_option('-q', '--quiet', dest = "quiet", 
                action = "store_true", default = False)
    parser.add_option('-o', '--output-file', dest="output", default=None)
    parser.add_option('-c', '--center', dest="center", default=False,
            help="For measuring colocalization distance, take as distance from"
            "the average colocalization", action="store_true")
    opts, args = parser.parse_args()
    
    
    if not opts.map:
        if opts.x1 and opts.x2 and opts.y1 and opts.y2:
            opts.xshift = opts.x2 - opts.x1
            opts.yshift = opts.y2 - opts.y1
    else:
        mapping = Analysis.loadmapping(opts.map)

    if opts.map2:
        mapping2 = Analysis.loadmapping(opts.map2)
    
    timepoints = defaultdict(list)
    tpmins = [0]*100
    tpmaxes = [0]*100
    
    imgname_finder = re.compile('(.*)_spot[0-9]+_[^_]+_xy(_only)?.txt')
    spotnum_finder = re.compile('spot([0-9]+)_')
    channel_finder = re.compile('spot[0-9]+_([0-9]{3})_xy(_only)?')

    #print map(glob, args) 
    
    max_timepoint = 0
    
    if len(args) == 1 and '*' in args[0]:
        args = glob(args[0])
    
    print "Found this many files", len(args)
    DQ_nomatch_x = []
    DQ_nomatch_y = []
    DQ_nomatch_t = []
    DQ_varbig_x = []
    DQ_varbig_y = []
    DQ_varbig_t = []
    DQ_toodim_x = []
    DQ_toodim_y = []
    DQ_toodim_t = []
    xr = []
    xl = []
    yr = []
    yl = []
    varxr = []
    varxl = []
    for fname in args:
        try:
            spotnum = int(spotnum_finder.findall(fname)[0])
            framenum = int(spotnum/100)
            imgname = imgname_finder.findall(fname)[0][0].rsplit('/')[-1] + '.tif'
            channel = channel_finder.findall(fname)[0][0]

            xs, ys, ns, lnums = array([ (float(line.split()[0]), 
                                     float(line.split()[1]), 
                                     float(line.split()[-1]),
                                     int(lnum)) 
                                for line, lnum in zip(file(fname), range(1,500)) 
                                  if line[0].isdigit()]).T
            lnums -= 2
            tpmin, tpmax = int(min(lnums)), int(max(lnums))
            if opts.framewise:
                max_timepoint = max(max_timepoint, tpmax)
                tpmaxes = array([max_timepoint, 0])
                tpmins = array([max_timepoint, 0])
                #print tpmaxes
                while len(timepoints[channel]) <= tpmax:
                    timepoints[channel].append([])
                for x, y, n, lnum in zip(xs, ys, ns, lnums):
                    lnum = int(lnum)
                    if n < opts.min_brightness:
                        DQ_toodim_x.append(x/opts.pxsize)
                        DQ_toodim_y.append(y/opts.pxsize)
                        DQ_toodim_t.append(lnum)
                    elif opts.flip:
                        timepoints[channel][lnum].append((x, 
                            512*opts.pxsize -  y, 
                            n))
                    else:
                        timepoints[channel][lnum].append((x, y, n))
            else:
                if tpmin < tpmins[framenum] or tpmax > tpmaxes[framenum]:
                    
                    tpmins[framenum] = int(tpmin)
                    tpmaxes[framenum] = int(tpmax)

                if len(xs) < 2: raise ValueError

                if std(sqrt(diff(xs)**2 + diff(ys)**2)/sqrt(2)) < opts.max_std:
                    if mean(ns) < opts.min_brightness:
                        DQ_toodim_x.append(mean(xs)/opts.pxsize)
                        DQ_toodim_y.append(mean(ys)/opts.pxsize)
                        DQ_toodim_t.append(framenum)
                        continue
                    while len(timepoints[channel]) <= framenum:
                        timepoints[channel].append([])
                
                    max_timepoint = max(max_timepoint, framenum)
                    if opts.flip:
                        timepoints[channel][framenum].append((mean(xs),
                                        512*opts.pxsize - mean(ys),
                                        sqrt(std(xs)**2 + std(ys)**2)))
                    else:
                        timepoints[channel][framenum].append((mean(xs), 
                                        mean(ys), 
                                        sqrt(std(xs)**2 + std(ys)**2)))
                else:
                    DQ_varbig_x.append(mean(xs)/opts.pxsize)
                    DQ_varbig_y.append(mean(ys)/opts.pxsize)
                    DQ_varbig_t.append(framenum)
        except ValueError:
            print "Not enough data in ", fname
            pass
        except:
            print "Failed on file", fname, "for some reason..."
            raise
    print "Max timepoint:", max_timepoint

    for channel in timepoints:
        print channel, ":", sum(map(len, timepoints[channel]))

    try:
        goodx = []
        goody = []
        newx = []
        newy = []
        diffx = []
        diffy = []
        framesetnum = []

        dists = []
        
        if opts.flip:
            opts.to_chan, opts.from_chan = opts.from_chan, opts.to_chan
        
        for i in range(max_timepoint):
            if len(timepoints[opts.from_chan]) <= i or \
                    len(timepoints[opts.to_chan]) <= i: 
                print "Bailing on timepoint", i
                continue
            else:
                pass
                #print "Processing timepoint ", i
            for x,y,e in timepoints[opts.from_chan][i]:
                if opts.map:
                    xn, yn = array(mapping(x/opts.pxsize,y/opts.pxsize)) * opts.pxsize
                    #yn += 10.18
                else:
                    xn = array([((x / opts.pxsize) + opts.xshift) * opts.pxsize])
                    yn = array([((y / opts.pxsize) + opts.yshift) * opts.pxsize])
                if xn == 0 or yn == 0:
                    continue
                bestx = 0
                besty = 0
                bestd = Inf
                beste = 0
                for x2, y2, e2 in timepoints[opts.to_chan][i]:
                    currd = (xn - x2)**2 + (yn - y2)**2
                    if currd < bestd:
                        bestd = currd
                        bestx = x2
                        besty = y2
                        beste = e2

                dists.append(bestd)
                goodx.append(bestx)
                goody.append(besty)
                newx.append(xn[0])
                newy.append(yn[0])
                diffx.append(bestx-xn)
                diffy.append(besty-yn)
                xr.append(x/opts.pxsize)
                yr.append(y/opts.pxsize)
                varxr.append(e)
                xl.append(bestx/opts.pxsize)
                yl.append(besty/opts.pxsize)
                varxl.append(beste)
                framesetnum.append(i)
                #print x, y, "\t", bestx, besty, "\t", xn, yn, math.sqrt(bestd)
            #print "Now up to a total of ", len(xr)
            for x,y, e in timepoints[opts.to_chan][i]:
                if x not in goodx and y not in goody:
                    DQ_nomatch_x.append(x/opts.pxsize)
                    DQ_nomatch_y.append(y/opts.pxsize)
                    DQ_nomatch_t.append(i)
        if opts.center:
            centerx = mean(diffx)
            centery = mean(diffy)
        else:
            centerx = 0
            centery = 0
        print len(diffx)
        assert len(varxl) == len(xl)
        for i in reversed(range(len(diffx))):
            # Count from the back so removing elements doesn't shift numbering
            if dists[i] is Inf or \
                    (diffx[i] - centerx)**2 + (diffy[i] - centery)**2 >= opts.max_r**2:
                DQ_nomatch_x.append(xr.pop(i))
                DQ_nomatch_y.append(yr.pop(i))
                fn = framesetnum.pop(i)
                DQ_nomatch_t.append(fn)
                goodx.pop(i)
                goody.pop(i)
                newx.pop(i)
                newy.pop(i)
                diffx.pop(i)
                diffy.pop(i)
                # xr and yr already popped
                varxr.pop(i)
                DQ_nomatch_x.append(xl.pop(i))
                DQ_nomatch_y.append(yl.pop(i))
                DQ_nomatch_t.append(fn)
                varxl.pop(i)
                # Framesetnum already popped
                continue
            assert len(xl) == len(varxl)
        print "New: ", len(diffx)
        diffx = array(diffx)
        diffy = array(diffy)
        newx = array(newx)
        newy = array(newy)
        goodx = array(goodx)
        goody = array(goody)
        xl = array(xl)
        yl = array(yl)
        xr = array(xr)
        yr = array(yr)
        varxl = array(varxl)
        varxr = array(varxr)
        framesetnum = array(framesetnum)
        
        print "Colocalized ", len(goodx), " spots at an average error of ", 
        print median(sqrt(diffx**2 + diffy**2)) 
        
        if opts.map2:
            print "Applying fiducials"
            xds, yds = mapping2(newx/opts.pxsize, newy/opts.pxsize)
            newx += xds 
            newy += yds 
            diffx = goodx - newx
            diffy = goody - newy
            print diffx[0], diffy[0]
            sel2 = (abs(xds - centerx) <  opts.max_R ) & (abs(yds-centery) <  opts.max_R) \
                    & (diffx < opts.max_R) & (diffy <  opts.max_R)
            
            diffx = diffx[sel2]
            diffy = diffy[sel2]
            goodx = goodx[sel2]
            goody = goody[sel2]
            xl = xl[sel2]
            yl = yl[sel2]
            xr = xr[sel2]
            yr = yr[sel2]
            newx = newx[sel2]
            newy = newy[sel2]
            varxl = varxl[sel2]
            varxr = varxr[sel2]
            framesetnum = framesetnum[sel2]
            
            print "In the second round, those colocalized at an error of",
            print median(sqrt(diffx**2 + diffy**2)) 
        elif opts.frame_map:
            new_goodx = []
            new_goody = []
            new_diffx = []
            new_diffy = []
            for i in range(1):#range(max(framesetnum)):
                #splitter = (framesetnum == 0)
                frame_select = array([True]*len(framesetnum))
                splitter = (rand(len(xl)) < opts.frame_map)
                #splitter = array([True]*len(framesetnum))
                
                num_spots_used = sum(frame_select & splitter)
                print "On Frame %d, using %d spots for regression" % (i, num_spots_used)
                if not num_spots_used: continue
                
                diffx_fids = diffx[frame_select & splitter]
                diffy_fids = diffy[frame_select & splitter]
                newx_fids = newx  [frame_select & splitter]
                newy_fids = newy  [frame_select & splitter]
                goodx_fids = goodx[frame_select & splitter]
                goody_fids = goody[frame_select & splitter]
                xl_fids = xl      [frame_select & splitter]
                yl_fids = yl      [frame_select & splitter]
                xr_fids = xr      [frame_select & splitter]
                yr_fids = yr      [frame_select & splitter]
                framesetnum_fids = framesetnum[frame_select & splitter]
                
                diffx_exp = diffx[frame_select  & ~splitter]
                diffy_exp = diffy[frame_select  & ~splitter]
                newx_exp = newx  [frame_select  & ~splitter]
                newy_exp = newy  [frame_select  & ~splitter]
                goodx_exp = goodx[frame_select  & ~splitter]
                goody_exp = goody[frame_select  & ~splitter]
                xl_exp = xl      [frame_select  & ~splitter]
                yl_exp = yl      [frame_select  & ~splitter]
                xr_exp = xr      [frame_select  & ~splitter]
                yr_exp = yr      [frame_select  & ~splitter]
                framesetnum_exp = framesetnum[frame_select  & ~splitter]
                
                if opts.save_map2:
                    mapping2 = Analysis.makeregression(diffx_fids, diffy_fids, 
                                            newx_fids, newy_fids, order=1,
                                            savefile = 'offsets'
                                                + os.path.splitext(os.path.basename(imgname))[0],)
                else:
                    mapping2 = Analysis.makeregression(diffx_fids, diffy_fids, 
                                            newx_fids, newy_fids, order=1)
                dx, dy = mapping2(newx_exp, newy_exp)
                newx_exp += dx
                newy_exp += dy
                
                new_goodx.extend(goodx_exp)
                new_goody.extend(goody_exp)
                new_diffx.extend(goodx_exp - newx_exp)
                new_diffy.extend(goody_exp - newy_exp)
            goodx = array(new_goodx)
            goody = array(new_goody)
            diffx = array(new_diffx)
            diffy = array(new_diffy)

            sel2 = (dx <  opts.max_R ) & (dy <  opts.max_R) \
                    & (diffx < opts.max_R) & (diffy <  opts.max_R)
            
            diffx = diffx[sel2]
            diffy = diffy[sel2]
            goodx = goodx[sel2]
            goody = goody[sel2]
            #xl = xl[sel2]
            #yl = yl[sel2]
            #xr = xr[sel2]
            #yr = yr[sel2]
            #newx = newx[sel2]
            #newy = newy[sel2]
            
            
            print "In the second round, those colocalized at an error of",
            print median(sqrt(diffx**2 + diffy**2)) 
            print "While keeping ", len(goodx), " spots"


            
        else:
            if opts.save_map2 \
               or raw_input('Save Second Pass? y/[n] ').lower() == 'y':
                mapping2 = Analysis.makeregression(diffx, diffy, xl, yl, 
                                        savefile= 'offsets'
                                            + os.path.splitext(os.path.basename(imgname))[0],
                                        order = int(max(2,sqrt(len(goody)/10))))
        
#   for x1,y1, x2,y2, e in zip(xr, yr, xl, yl, varxl):
#       if opts.map:
#           print "#", x1, y1, "\t", x2, y2, "\t", array(mapping(x1, y1)).T, "\t\t", math.sqrt(e)
    except IndexError:
        print "Not enough data!"
    finally:
        try:
            print "Saving to ", os.path.dirname(fname)+'.mat'
            output_dict = {}
            for var in ('xl', 'yl', 'xr', 'yr', 'varxl', 'varxr', 'newx', 'newy',
                        'diffx', 'diffy',
                        'framesetnum', 'tpmins', 'tpmaxes', 'imgname', 
                        'DQ_varbig_x','DQ_varbig_y', 'DQ_varbig_t',
                        'DQ_nomatch_x', 'DQ_nomatch_y', 'DQ_nomatch_t',
                        'DQ_toodim_x', 'DQ_toodim_y', 'DQ_toodim_t'):
                if var in dir():
                    exec 'output_dict["%s"] = %s' % (var, var)      
            
            if opts.frame_map:
                for var in ('xl_fids', 'yl_fids', 'xr_fids', 'yr_fids', 
                            'xl_exp', 'yl_exp', 'xr_exp', 'yr_exp',
                            'framesetnum_fids', 'framesetnum_exp'):
                    if var in dir():
                        exec 'output_dict["%s"] = %s' % (var, var)
            output_dict['framebyframe'] = opts.framewise
            output_dict['mapname'] = opts.map
            output_dict['mapname2'] = opts.map2
            
            io.savemat(opts.output or os.path.dirname(fname) + '.mat', output_dict)
        except IOError:
            print "Couldn't save a .mat file.  Probably a filesystem issue"
    if not opts.quiet:
        ion()
        figure()
        Q = quiver(goodx, goody, diffx, diffy, angles='xy', minshaft=2, units='x')
        scale = math.sqrt(median(array(diffx)**2 + array(diffy)**2)) 
        title('%s with mapping %s and error < %d' % 
            (os.path.dirname(fname) ,str(opts.map or opts.yshift), opts.max_r))
        print scale
        if scale < 50:
            quiverkey(Q, .1, .1, 10, '$10 nm$', color="blue")
        else:
            quiverkey(Q, .1, .1, 1000, r'$1\mu m$', color="blue")
        figure()
        plot(diffx, diffy, 'ro')
        title(os.path.dirname(fname))

    for channel in timepoints:
        num = sum(len(timepoint) for timepoint in timepoints[channel])
        print channel, num
