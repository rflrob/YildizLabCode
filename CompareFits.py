import Analysis
from scipy.special import jn

def bessel(center_x, center_y, width_x, width_y, offset, height):
	"""returns a 2-D bessel function with the given parameters
	"""
	
	def bessel_func(x,y):
		R = sqrt((x - center_x)**2/width _ x + (y - center_y)**2 / width_y)
		return offset + height * jn(0, R)
		
	
	return bessel_func

		
def quasi_airy(center_x, center_y, width_x, width_y, offset, height):
	def quairy_func(x,y):
		R = sqrt((x - center_x)**2/width_x + (y - center_y)**2 / width_y)
		return offset + height * jn(1, R)/(R+1e-6)
	
	return quairy_func


if __name__ == '__main__':
	funcs = {"Quasi-Airy": quasi_airy, "Gaussian": Analysis.gaussian, \
				"Airy" : Analysis.airy, "Bessel", bessel}
	rmses = {}			
	for i in funcs.keys():
		rmses[i] = 0
	
	try:
		os.uname()
		dirname = '/Users/pcombs/Documents/RotationData/2009-12-08-FITS/*'
		bgname = '/Users/pcombs/Documents/RotationData/2009-12-08/MED_2009-12-08.fits'
	except AttributeError:
		dirname = r'C:\Documents and Settings\admin\Desktop\Peter\2009-12-09-FITS/8*'
		bgname = r'C:\Documents and Settings\admin\Desktop\Peter\MED_2009-12-08.fits'

	filelist = glob(dirname)
	filelist = [os.path.join(dirname, f) for f in filelist]
	filelist = filelist
	
	for func_name in funcs.keys():
		fit = Analysis.fit2d(xs, ys, data, fcn = funcs[func_name])