import os
import subprocess
import time
from datetime import datetime
import numpy as np
import threading
import pcapy
import socket
import csv

start_time = time.time()
ip_address = None
etx_value = None
packetsize_avg = None
etx2filt = []
etx3filt = []
ett_dict = {}
etx_dict = {}
cont_dict = {}
cont_value = []

#Fuction to listen to Controller status broadcast signal. 
#The Controller Status and IP address is then stored in a global dictionary.
def radio():
	global cont_dict
	count = 0
	MYPORT = 10000
	s1 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	s1.bind(('', MYPORT))
	print "radio thread started\n"
	while 1:
		data, wherefrom = s1.recvfrom(1500, 0)
		cont_dict[''+wherefrom[0]+''] = data.strip('\n')

#This function interacts with the OLSRd software are obtains the ETX value. 
#The ETX value and corresponding IP addresses are written onto a dictionary. 
def recieve():
	global ip_address, etx_dict
	print "recieve thread started\n"
	
	UDP_IP = "10.10.10.5"
	UDP_PORT = 9999
	
	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	sock.bind((UDP_IP, UDP_PORT))
	while True:
		data, addr = sock.recvfrom(2048)
		data_extracted = data.split('-')
		ip_address = data_extracted[1]
		etx = data_extracted[2].strip('\0')
		if etx != 'INFINITE':
			if ip_address == "10.10.10.2":
				etx2filt.append(float(etx))
			else:
				etx3filt.append(float(etx))
			if len(etx2filt) == 5:
				etx = sum(etx2filt)/float(len(etx2filt))
				etx_dict[''+ip_address+''] = etx
				print "IP address = ", ip_address
				print "ETX value = ", etx
				print "---------------------------------------"
				del etx2filt[0]
			if len(etx3filt) == 5:
				etx = sum(etx3filt)/float(len(etx3filt))
				etx_dict[''+ip_address+''] = etx
				print "IP address = ", ip_address
				print "ETX value = ", etx
				print "---------------------------------------"
				del etx3filt[0]

def mainfunction():
	global ip_address, etx_dict, ett_dict, start_time, cont_value, cont_dict
	print "Main function started\n"
	
	while True:
		if len(cont_dict) == 2 and len(etx_dict) == 2:
			for key, value in cont_dict.iteritems():
				for key1, value1 in etx_dict.iteritems():
					if key == key1 and value1 != 'INFINITE':
						print "IP Address = ", key
						print "ETX value = ", value1
						print "---------------------------------------"
						if len(cont_value) == 2:
							with open("test.txt", "a+") as myfile:
								myfile.write("%f, %s, %f, %d\n" % (float(time.time() - start_time),key,float(value1), cont_value[1]))
								time.sleep(4)
			
def handoff():
	global etx_dict, ett_dict, cont_value, cont_dict
	old_controller = None
	cont_value = [2,2]
	while True:
		if len(etx_dict) == 2 and etx_dict.values()[0] != 'INFINITE' and etx_dict.values()[1] != 'INFINITE' and len(cont_dict) == 2:
			if etx_dict.values()[0] < etx_dict.values()[1]:
				cont_value.append(2)
				del cont_value[0]
				new_controller = etx_dict.keys()[0]
				if cont_value[0] == cont_value[1] and old_controller != new_controller:
					print "hand-off initiated"
					print "Controller set to %s" % etx_dict.keys()[0]
					print "---------------------------------------"
					response = os.system("echo iist@123 | sudo ovs-vsctl set-controller br0 tcp:%s:6633 > /dev/null 2>&1" % str(etx_dict.keys()[0]))
					old_controller = new_controller
			else:
				cont_value.append(4)
				del cont_value[0]
				new_controller = etx_dict.keys()[1]
				if cont_value[0] == cont_value[1] and old_controller != new_controller:
					print "hand-off initiated"
					print "controller set to %s" % etx_dict.keys()[1]
					print "---------------------------------------"
					response = os.system("echo iist@123 | sudo ovs-vsctl set-controller br0 tcp:%s:6633 > /dev/null 2>&1" % str(etx_dict.keys()[1]))
					old_controller = new_controller

rad = threading.Thread(name='radio', target=radio)		
r = threading.Thread(name='recieve', target=recieve)
m = threading.Thread(name='mainfunction', target=mainfunction)
h = threading.Thread(name='handoff', target=handoff)

rad.start()
r.start()
time.sleep(2)
m.start()
time.sleep(2)
h.start()
