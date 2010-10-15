import scipy.linalg as la
import numpy as np

def fitgauss(data, err = 1e-4, xs = None, ys = None):
	"""Based on the fitgauss.m function written by Xiaolin Nan
	"""
	
	s = np.shape(data)
	
	if xs == None or ys == None:
		ys, xs = np.indices(s) + 1
	
	estimate = np.empty(5)
	
	peak_ind = data.argmax()
	
	estimate[0] = data.mean() 				# Background
	estimate[1] = data.max() - estimate[0] 	# Amplitude
	estimate[2] = xs.flat[peak_ind] 		# x0
	estimate[3] = ys.flat[peak_ind] 		# y0
	estimate[4] = 1.0						# sig
	
	jg = np.ones((np.size(data), 5))
	diff = np.empty((np.size(data),1))
	
	for i in range(10):
		pexp = estimate[1] * \
			np.exp(-((xs - estimate[2])**2 + (ys - estimate[3])**2)
					/(2*estimate[4]**2))
		jg[:,1] = np.ravel(pexp / estimate[1])
		jg[:,2] = np.ravel((xs - estimate[2]) * pexp / estimate[4]**2)
		jg[:,3] = np.ravel((ys - estimate[3]) * pexp / estimate[4]**2)
		jg[:,4] = np.ravel(((xs - estimate[2])**2 + (ys - estimate[3])**2) \
					* pexp / estimate[4]**3)
		diffm = np.ravel(estimate[0] + pexp - data)
		
		
		[dlambda, residues, rank, s] = la.lstsq(jg, diffm)
		
		estimate -= dlambda
		if dlambda[2] < err and dlambda[3]<err:
			break
	return estimate