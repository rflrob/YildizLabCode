### QueueTest.py


from multiprocessing import Queue, Pool, Manager
from sys import getsizeof


def addtoqueue(i, queue):
	"""docstring for addtoqueue"""
	pass


if __name__ == '__main__':
	q = Queue()
	m = Manager()
	
	l = m.list()

	print 'Queue Starting Size:', getsizeof(q)
	print 'List Starting Size:', getsizeof(l)

	for i in range(10000000):
		if q.full(): 
			print "Oh no! Queue is full after only %d iterations" % i
		l.append((i, 2.1, 2.2, 2.3, 2.4))
		if i % 10000 == 0: print i
	
	print 'Queue Full Size: ', getsizeof(q), ' (', getsizeof(q)/1024**2, ' MB)'
	print 'List Full Size: ', getsizeof(l), ' (', getsizeof(l)/1024**2, ' MB)'

	while not q.empty():
		q.get()
	