from glob import glob
from os import path
from matplotlib.pyplot import figure, subplot, hist, title, show
from numpy import arange, pi
import platform
from functools import reduce

mol_rad = "0.001"
plot_as_polar = True
show_individuals = True
min_sep = 5
max_sep = 35

if 'Win' in platform.system():
    basedir = 'F:/Peter/'
elif 'Darwin' in platform.system():
    basedir = '/Volumes/NewVolume/Peter'
else:
    basedir = ''

dirs = {122: ['2010-09-12'], 
        124:['2010-09-12'],
        125: ['2010-09-13'], 
        592:['2010-09-27']}

rotations = {122: '-3', 124: '-4', 125: '-7', 592: 'WT'}

plottypes = [592, 125, 122]

#######################################################################


def get_data(data_dirs, types_in_dirs):
    adx = []
    ady = []
    ae = []
    aaa = []

    for datadir in data_dirs:
        for dyntype in types_in_dirs:
            for mtfile in glob(path.join(basedir,datadir, 'Dyn%s*-MTs.txt'%dyntype)):
                mtfile = mtfile.replace('\\', '/')

                matfile = glob(mtfile.split('-MTs')[0]+'*.mat')[0]
                matfile = matfile.replace('\\', '/')

                if not path.isfile(matfile):
                    print "*"*70
                    print "Can't find '", matfile, "' in ", dir
                    print "*"
                    continue

                _ip.magic("run AlignToAxos -r " + mol_rad+ " " + matfile + " " +
                    mtfile)
                print "run AlignToAxos -r " + mol_rad+ " " + matfile + " " + mtfile
                adx.extend(dxs); ady.extend(dys); ae.extend(es); aaa.extend(all_axo_angles)
    return adx, ady, ae, aaa
 
oldsep = path.sep
path.sep = '/'

numrows = 2 + show_individuals

#for enumed, dyntype in enumerate(plottypes):
#    adx = []; ady = []; ae = []; aaa = [];
#    for datadir in dirs[dyntype]:
#        for mtfile in glob(path.join(basedir,datadir, 'Dyn%s*-MTs.txt'%dyntype)):
#            mtfile = mtfile.replace('\\', '/')
#            
#            matfile = glob(mtfile.split('-MTs')[0]+'*.mat')[0]
#            matfile = matfile.replace('\\', '/')
#
#            if not path.isfile(matfile):
#                print "*"*70
#                print "Can't find '", matfile, "' in ", dir
#                print "*"
#                continue
#            
#            _ip.magic("run AlignToAxos -r " + mol_rad+ " " + matfile + " " +
#                    mtfile)
#            print "run AlignToAxos -r " + mol_rad+ " " + matfile + " " + mtfile
#            adx.extend(dxs); ady.extend(dys); ae.extend(es); aaa.extend(all_axo_angles)
    
rotvals = sorted(set([rotations[type] for type in plottypes]))
for enumed, rot in enumerate(rotvals):
    types = [key for key in rotations if rotations[key] == rot and key in
             plottypes]
    curr_dirs = reduce(append, [dirs[type] for type in dirs if type in types],[])
    adx, ady, ae, aaa = get_data(curr_dirs, types)
    figure(2)
    c,r,t = as_polar_with_errors(adx, ady, ae, aaa, 'g')
    s = (min_sep < r) & (r < max_sep)
    figure(1)

    # Plot the Distance histograms
    subplot(numrows,len(rotvals), enumed+1)
    title('%s' % rot)
    hist(r, arange(0, 45, 2))
    
    # Plot the angle histograms
    subplot(numrows,len(rotvals),len(rotvals) + enumed + 1, polar=plot_as_polar)
    hist((t + 10*pi)%(2*pi), arange(0,361, 15)*pi/180)

    if show_individuals:
        subplot(3, len(rotvals), len(rotvals) * 2 + enumed + 1, polar=True)
        polar(t[s], r[s], 'x')



path.sep = oldsep
show()
