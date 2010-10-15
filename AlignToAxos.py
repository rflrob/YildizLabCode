import sys, math, numpy
from optparse import OptionParser 
from scipy.io import loadmat
from collections import defaultdict
from pylab import dist_point_to_segment
from matplotlib import  patches, \
        projections, transforms, collections
from matplotlib.pyplot import polar, gca, text, figure
from numpy import mean, sqrt

class rangedict(defaultdict):
    """ An extension of the defaultdict type. 
    
    Keys are pairs, and when a __getitem__ is called, if the key is not one of the
    pairs already in the dictionary, it will return a value if the key is
    between the two elements of the pair."""
    def __missing__(self, key):
        if isinstance(key, tuple):
            self[key] = []
            return self[key]
        else:
            try:
                reslist = []
                for pair in self:
                    if pair[0] <= key <= pair[1]:
                        reslist.extend(self[pair])
                return reslist 

            except IndexError:
                raise TypeError("Badly formed dictionary.  Keys should be pairs")    
            raise KeyError(key)


def as_polar_with_errors(xs, ys, errs, angs, color='r'):
    ax = gca(polar=True)
    xs = numpy.array(xs)
    ys = numpy.array(ys)

    rs = sqrt(xs**2 + ys**2)
    ths= numpy.arctan2(ys, xs)

    es = [patches.Ellipse(xy=(x,y), width=1.4*err, height=1.4*err)
            for x,y,err in zip(xs, ys, errs)]
    
    tr = ax.InvertedPolarTransform()
    ret = []
    for i, e in enumerate(es):
        rot = transforms.Affine2D().rotate(-angs[i])
        path = e.get_path()
        pnew = e.get_patch_transform().transform_path(path)
        pnew = rot.transform_path(pnew)
        pnew = tr.transform_path(pnew)
        pnew = patches.PathPatch(pnew)
        pnew.set_facecolor(color) 
        ret.append(pnew)
        text(ths[i]-angs[i], rs[i], '%d'%i, 
                horizontalalignment='center', 
                verticalalignment='center')
    coll = collections.PatchCollection(ret, alpha=.5, facecolor=color)
    coll.set_facecolor(color)
    ax.add_collection(coll)
    return coll, rs, ths - angs

def get_pairdata(datafname):
    """ returns a list of pair-wise datapoints:
        each data point is a tuple:
        (framenumbers, x655, y655, x585, y585, screenx, screeny)

        where screenx and screeny should be used for finding the nearest axoneme
        """
    Data = loadmat(datafname)
    if Data.has_key('pxsize'):
        pxsize = Data['pxsize']
    else:
        pxsize = 106.667

    x655 = Data['xl'] * pxsize
    y655 = Data['yl'] * pxsize
    x585 = Data['newx']
    y585 = Data['newy']
    screenx = Data['xr']
    screeny = Data['yr']
    framenums = Data['framesetnum']
    
    # apologies for this ugly map stuff... it's to get the arrays into just plain numbers
    return map(lambda x: map(lambda y: y[0], x), 
            zip(framenums, x655, y655, x585, y585, screenx, screeny))
   

import pdb
def get_axodata(axofname):
    """ """
    results = rangedict(list)
    for lnum, usline in enumerate(file(axofname)):
        if not usline[0].isdigit():
            continue
        line = map(int,usline.split())
        if len(line) != 6:
            raise IOError('Badly formed file:\n#%d: %s' % (lnum, usline))
        results[line[0], line[1]].append(((line[2], line[3]), 
                                          (line[4], line[5])))
    return results
    
        
if __name__ == "__main__":
    parser = OptionParser(usage="Usage: %progname [options] WHSpotData.mat"
                          " AxoData.txt")
    parser.add_option('-r', '--distance', dest='r', default=50, type="float",
            help="For finding distinct molecules, the separation beyond which "
            "it will be called a new molecule")
    opts, args = parser.parse_args()

    if len(args) != 2:
        parser.print_usage()
        sys.exit()
    
    # Read in the data
    pair_data = get_pairdata(args[0])
    axo_data = get_axodata(args[1])

    # Associate each point pair with the nearest axoneme
    pairs_on_axos = defaultdict(list)
    
    for pair in pair_data:
        mindist = 10
        nearaxo = None
        for axo in axo_data[pair[0]]:
            dist = dist_point_to_segment((pair[-2], pair[-1]), axo[0], axo[1])
            if dist < mindist:
                dist = mindist
                nearaxo = axo
        pairs_on_axos[nearaxo].append(pair)
    print "Peter, you idiot!  Didn't find axos for frames:"
    print set(map(lambda x: x[0], pairs_on_axos[None]))


    # Find orientation of each pair with respect to the nearest axoneme
    all_rs = []
    all_thetas = []
    
    for axo in pairs_on_axos:
        if axo is None: continue
        
        vec = (axo[0][0] - axo[1][0]),(axo[0][1] - axo[1][1])
        axo_angle = math.atan2(vec[1], vec[0])
        rs = [math.sqrt((p[1] - p[3])**2 + (p[2] - p[4])**2) 
              for p in pairs_on_axos[axo]]
        thetas = [math.atan2(p[2] - p[4], p[1] - p[3]) - axo_angle
              for p in pairs_on_axos[axo]]
        all_rs.extend(rs)
        all_thetas.extend(thetas)
        
    all_axo_angles = []
    all_axos = []
    all_clusters = []
    dxs = []
    dys = []
    es = []

    for axo in pairs_on_axos:
        if axo is None: continue

        vec = (axo[0][0] - axo[1][0]),(axo[0][1] - axo[1][1])
        axo_angle = math.atan2(vec[1], vec[0])
        
        clusters = []
        for pair in pairs_on_axos[axo]:
            best_cluster = None
            for cluster in clusters:
                mx = mean([p[-2] for p in cluster])
                my = mean([p[-1] for p in cluster])
                x = pair[-2]
                y = pair[-1]
                if (x-mx)**2 + (y - my)**2 < opts.r:
                    best_cluster = cluster
            if best_cluster:
                best_cluster.append(pair)
            else:
                clusters.append([pair])
        dx = [mean([p[1] - p[3] for p in cluster]) for cluster in clusters]
        dy = [mean([p[2] - p[4] for p in cluster]) for cluster in clusters]
        e = [math.sqrt(mean([(p[1] - p[3] - dx[i])**2 
                            + (p[2] - p[4] - dy[i])**2 for p in cluster]))
                for i, cluster in enumerate(clusters)]
        
        all_clusters.extend(clusters)
        all_axo_angles.extend([axo_angle]*len(clusters))
        all_axos.extend([axo]*len(clusters))

        dxs.extend(dx)
        dys.extend(dy)
        es.extend(e)
   
    es = numpy.array(es)
    dxs = numpy.array(dxs)
    dys = numpy.array(dys)
