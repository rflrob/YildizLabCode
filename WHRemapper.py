import Analysis
import sys
from numpy import array, sqrt, isnan
from pylab import plot, legend, xlabel, ylabel, title, figure

Nm_per_pixels = 106.66

print "Reading map from ", sys.argv[1]

mapping = Analysis.loadmapping(sys.argv[1])

print "Reading 585 Channel from ", sys.argv[2]
f585 = open(sys.argv[2])
x585, y585 = zip(*[map(float, l.split()) for l in f585])
print "Reading 655 Channel from ", sys.argv[3]
f655 = open(sys.argv[3])
x655, y655 = zip(*[map(float, l.split()) for l in f655])


# Convert to numpy arrays for easier handling
x655 = array(x655)
y655 = array(y655)
x585 = array(x585)
y585 = array(y585)

# Rescale to pixels
x655 /= Nm_per_pixels
y655 /= Nm_per_pixels
x585 /= Nm_per_pixels
y585 /= Nm_per_pixels

# Correct for the clipping done for mapping (See box1, box2 in Analysis.py)
#x655 -= 3
#x585 -= 3
#y655 -= 260
#y585 -= 6


# Remap the 655 ('right hand') channel 
x655m, y655m = mapping(x655, y655)


mmdOrigz = sqrt((x585 - x585[~isnan(x585)][0] - x655 + x655[~isnan(x655)][0])**2 \
				+ (y585 - y585[~isnan(y585)][0] - y655 + y655[~isnan(y655)][0])**2)*106
mmdRemapz = sqrt((x585 - x585[~isnan(x585)][0] - x655m + x655m[~isnan(x655m)][0])**2 \
				+ (y585 - y585[~isnan(y585)][0] - y655m + y655m[~isnan(y655m)][0])**2)*106.6

mmdOrig = sqrt((x585 - x655)**2 \
				+ (y585  - y655)**2)*Nm_per_pixels
mmdRemap = sqrt((x585 - x655m)**2 \
				+ (y585 - y655m)**2)*Nm_per_pixels

while True:
	outname = raw_input('File to save remapped coordinates: ')	
	if outname[-4:] == '.txt':
		outfile = open(outname, 'w')
		for x,y in zip(x655m, y655m):
			outfile.write('%02f\t%02f\n'%(x * Nm_per_pixels, y * Nm_per_pixels))
		break
	elif outname[-4:] == '.mat':
		from scipy.io import savemat
		savemat(outname, {'x655_remap': x655m*Nm_per_pixels, 'y655_remap': y655m * Nm_per_pixels})
		break
	else:
		print "Unrecognized extension.  Use .mat or .txt"
plot(mmdOrig)
plot(mmdRemap)
legend(('Original Mismatch Distance', 'Remapped Mismatch Distance'))
xlabel('Frame Number')
ylabel('Mismatch ')

figure()
plot(mmdOrigz)
plot(mmdRemapz)
legend(('Original Mismatch Distance', 'Remapped Mismatch Distance'))
xlabel('Frame Number')
ylabel('Mismatch after zeroing')


improve = mmdOrig - mmdRemap
improvez = mmdOrigz - mmdRemapz

figure()
plot(improve)
ylabel('Improvement by Mapping (nm)')
xlabel('Frame Number')

figure()
plot(improvez)
ylabel('Improvement by Mapping after zeroing (nm)')
xlabel('Frame Number')
