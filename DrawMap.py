import Analysis, sys, math, numpy as np, pylab

mapping = Analysis.loadmapping(sys.argv[1])


num_rows = 256
num_cols = 512
colors = np.zeros((256,512,3))

starty = np.random.rand(1,100)*150 + 50
startx = np.random.rand(1,100)*400 + 50
endx, endy = mapping(startx, starty)

base_shift_x = 256 # (endx - startx).mean()
base_shift_y = 512 # (endy - starty).mean()


for x in range(num_cols):
	for y in range(num_rows):
		newx, newy = mapping(x,y)
		sat = 1
		hue = (90 + 180 / math.pi * math.atan2(newy - base_shift_y, newx - base_shift_x)) % 360
		val = min(.001 * math.sqrt((newy - base_shift_y)**2 + (newx - base_shift_x)**2), 1)

		hueprm = hue / 60
		C = val * sat
		X = C * (1 - abs((hueprm %2) -1 ))
		
		if hueprm < 1: r1, g1, b1 = C, X, 0
		elif hueprm < 2: r1, g1, b1 = X, C, 0
		elif hueprm < 3: r1, g1, b1 = X, C, 0
		elif hueprm < 4: r1, g1, b1 = X, C, 0
		elif hueprm < 5: r1, g1, b1 = X, C, 0
		elif hueprm < 6: r1, g1, b1 = X, C, 0
		else:
			print "OH NOES!!!"
		
		m = val - C
		colors[y,x,:] = [r1 + m, g1 + m, b1 + m]

pylab.figure()
pylab.imshow(colors)
pylab.title(sys.argv[1])