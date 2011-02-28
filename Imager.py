import time
import numpy.ctypeslib as ctl
import ctypes
import multiprocessing as mp
import Analysis
from numpy import ones, zeros, arange, floor, array, empty, int32, float32

# img[l/r]_box is a Matlab style [x y w h] box descriptor
default_imgl_box = [17,         1,      241,    512]
default_imgr_box = [257,        1,      256,    512]

double4 = ctypes.c_double*4

def move_and_image(mmc, e7xx, id, coords, exptime, image_queue, **kwargs):
	"""
	move_and_image moves the stage to the given coordinates, takes an
	exposure for exptime seconds, then adds it to image_queue.
	"""

	DEBUG = False
	
	for key in kwargs:
		if key == 'DEBUG': DEBUG = True
		else: raise TypeError, 'Unknown argument "%s"' % key

	if DEBUG: print "Moving to ", coords
	err = e7xx.E7XX_MOV(id, "14", ctl.as_ctypes(array(coords, dtype=float)))
	
	if err:
		print "Moved OK"
	else:
		err = e7xx.E7XX_GetError(id)
		print err
		
	time.sleep(.03)
	if DEBUG:
		res = ctl.as_ctypes(empty(4, dtype=float))
		e7xx.E7XX_qMOV(id, "14", res)
		print "Moved to ", ctl.as_array(res)
	
	noImage = True
	
	while noImage:
		try:
			if image_queue.qsize() < 1000:
				if DEBUG: print "Snapping Image"
				mmc.snapImage()
				im1 = mmc.getImage()
				if DEBUG: print "Got image"
				image_queue.put(im1)
				if DEBUG: print "Queueing image"
				noImage = False
				if DEBUG: print "Leaving Loop"
		except MemoryError:
			if DEBUG: print "Memory Error.  Going to sleep"
			time.sleep(1)
	if DEBUG: print "Done"
			

def process_image(img_queue, coords_queue, imgl_box = default_imgl_box, imgr_box = default_imgr_box):
	"""docstring for process_image"""
	while True:
		if not img_queue.empty():
			img = img_queue.get()
			imgl = img[imgl_box[1] - 1:imgl_box[1] - 1 + imgl_box[3], \
						imgl_box[0] - 1:imgl_box[0] - 1 + imgl_box[2]]
			imgr = img[imgr_box[1] - 1:imgr_box[1] - 1 + imgr_box[3], \
						imgr_box[0] - 1:imgr_box[0] - 1 + imgr_box[2]]
			
			
			
		else:
			time.sleep(1)


def setup_stage():
	"""docstring for setup_stage
	"""
	import ctypes
	
	e7xx = ctypes.windll.LoadLibrary('E7XX_GCS_DLL.dll')
	try:
		print "Connecting to stage"
		id = e7xx.E7XX_ConnectRS232(1, 57600)

		print "Initializing axes"
		e7xx.E7XX_INI(id, '134')

		print "initializing servos"
		err = e7xx.E7XX_SVO(id, '134', ctl.as_ctypes(ones(4, dtype=int32)))
		if err:
			print "Servos initialized OK"
		else:
			import sys
			sys.exit(e7xx.E7XX_GetError(id))
		svo = ctl.as_ctypes(ones(4, dtype=int32))
		err = e7xx.E7XX_qSVO(id, '134', svo)
		if err:
			print "Read servos OK"
		else:
			print e7xx.E7XX_GetError(id)
			time.sleep(5)
		
		while not(all(ctl.as_array(svo))):
			e7xx.E7XX_qSVO(id, '134', svo)
			print "Servo status: ", ctl.as_array(svo), ctl.as_array(svo).all()
			time.sleep(1)

	finally:
		return e7xx, id


def setup_camera():
	"""docstring for setup_camera"""
	import os
	currdir = os.getcwd()
	os.chdir(r'C:\Program Files\Micro-Manager-1.3')
	import MMCorePy
	mmc = MMCorePy.CMMCore()
	
	mmc.loadDevice("andor", "Andor", "Andor")
	mmc.initializeAllDevices()

	os.chdir(currdir)
	
	return mmc

	
def main(w = 30, h = 30, stepsize = 0.1, exposure = 0.1):
	"""docstring for main"""
	
	mmc = setup_camera()
	e7xx, stageid = setup_stage()
	
	
	nr = h/stepsize + 1
	nc = w/stepsize + 1
	
	ran = arange(nr * nc)
	yi = floor(ran / nc)
	ys = yi * stepsize
	xi = (yi %2) * (nc - ran % nc - 1) + (1 - yi % 2) * (ran % nc)
	xs = xi * stepsize
	
	
	img_queue = mp.Queue()
	coords_queue = mp.Queue()
	try:
		for coord in zip(xs, ys):
			move_and_image(mmc, e7xx, stageid, coord, exposure, img_queue, \
				       DEBUG = True)
	finally:
		while not (img_queue.empty()):
			img_queue.get()
		mmc.unloadAllDevices()
		e7xx.E7XX_CloseConnection(stageid)

			
if __name__ == '__main__':
	main()

