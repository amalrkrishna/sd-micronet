# Send UDP broadcast packets

MYPORT = 8000

import sys, time
from socket import *
import threading

def broadcast():
	
	s = socket(AF_INET, SOCK_DGRAM)
	s.bind(('', 0))
	s.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
	print 'broadcast'
	while 1:
		data = repr(time.time()) + '\n'
		s.sendto(data, ('<broadcast>', MYPORT))
		time.sleep(2)

def radio():
	
	s1 = socket(AF_INET, SOCK_DGRAM)
	s1.bind(('', MYPORT))
	print 'radio'
	while 1:
		data, wherefrom = s1.recvfrom(1500, 0)
		sys.stderr.write(repr(wherefrom) + '\n')
		sys.stdout.write(data)

b = threading.Thread(name='broadcast', target=broadcast)
r = threading.Thread(name='radio', target=radio)

b.start()
time.sleep(1)
r.start()
