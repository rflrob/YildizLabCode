mapbase = '../../2010-06-07/0607-Crimson_1_200'
dataname = '../../2010-06-07/0607-Crimson.mat'

mappingC = Analysis.loadmapping(mapbase)
CData = io.loadmat(dataname)

xr = CData['xr']; yr = CData['yr']; xl = CData['xl']; yl = CData['yl'];
xn, yn = mappingC(xr, yr)

diffmag = sqrt((xn - xl)**2 + (yn - yl)**2).T;
hist(diffmag*106.667, arange(0,100, 1))

sel = diffmag*106.667 < 10;

xlg = xl.T[sel]; ylg = yl.T[sel]; xrg = xr.T[sel]; yrg = yr.T[sel];
xn, yn = mappingC(xrg, yrg)
diffx = xlg - xn
diffy = ylg - yn
diffmag = sqrt(diffx**2 + diffy**2)
diffxs = zeros((ceil(yr.max())+2, ceil(xr.max())+2))
diffys = zeros((ceil(yr.max())+2, ceil(xr.max())+2))
ns = zeros(shape(diffxs))

ns += 1e-10
#diffxs += 1e-10
#diffys += 1e-10

for c, r, xd, yd in zip(xrg, yrg, diffx, diffy):
        c = round(c)
        r = round(r)
        diffxs[r,c] += xd
        diffys[r,c] += yd
        ns[r,c] += 1

xs, ys = meshgrid(range(ceil(xr.max())+2), range(ceil(yr.max())+2))

ax = (diffxs/ns).flatten()
ay = (diffys/ns).flatten()


figure(); quiver(x[ax*ay!=0], y[ax*ay != 0], ax[ax*ay != 0], ay[ax*ay != 0], units='x')
figure(); contourf(ns.clip(0,16)); colorbar(); title('ns')

len(sel)
sum(sel)
sum(~sel)
Analysis.makeLSQspline(xlg, ylg, xrg, yrg, n=200, savefile=mapbase.replace("_1_200", "_2"))
