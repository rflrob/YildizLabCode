from glob import glob
from os import path
from matplotlib.pyplot import figure, subplot, hist

mol_rad = "0.001"
dirs = {122: ['F:/Peter/2010-09-12'], 124:['F:/Peter/2010-09-12'],
        125: ['F:/Peter/2010-09-13'], 592:['F:/Peter/2010-09-13']}

rotations = {122: '-7', 124: '-3', 125: '-4', 592: 'WT'}

plottypes = [592, 125, 122]

oldsep = path.sep
path.sep = '/'

for enumed, dyntype in enumerate(plottypes):
    adx = []; ady = []; ae = []; aaa = [];
    for datadir in dirs[dyntype]:
        for mtfile in glob(datadir + '/'+ 'Dyn%s*-MTs.txt'%dyntype):
            
            matfile = glob(mtfile.split('-MTs')[0]+'*.mat')[0]

            if not path.isfile(matfile):
                print "*"*70
                print "Can't find '", matfile, "' in ", dir
                print "*"
                continue
            
            _ip.magic("run AlignToAxos -r " + mol_rad+ " " + matfile + " " +
                    mtfile)
            print "run AlignToAxos -r " + mol_rad+ " " + matfile + " " + mtfile
            adx.extend(dxs); ady.extend(dys); ae.extend(es); aaa.extend(all_axo_angles)

    figure(2)
    c,r,t = as_polar_with_errors(adx, ady, ae, aaa, 'g')
    figure(1)
    subplot(2,len(plotttypes), enumed+1)
    title('Dyn %s (%s)' % (dyntype, rotations[dyntype]))
    hist(r, arange(0, 45, 2))
    subplot(2,len(plottypes),len(plottypes) + enumed + 1, polar=True)
    hist((t + 10*pi)%(2*pi), arange(0,361, 15)*pi/180)


path.sep = oldsep
