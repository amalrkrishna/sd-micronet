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
rtt_dict = {}
cont_dict = {}
rtt2filt = []
rtt3filt = []
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
		
def rttcal(ip_address):
	rttcal = subprocess.check_output("ping -c 5 " + ip_address + "| tail -1| awk '{print $4}' | cut -d '/' -f 2", shell=True)
	return rttcal

def mainfunction():
	global ip_address, start_time, cont_value, cont_dict, rtt_dict
	print "Main function started\n"
	
	while True:
		for key, value in cont_dict.iteritems():
			rtt = rttcal (key)
			print "IP Address = ", key
			if len(cont_value) == 2: 
				with open("test.txt", "a+") as myfile:
					myfile.write("%f, %s, %f, %d\n" % (float(time.time() - start_time),key,float(rtt), cont_value[1]))
			if key == "10.10.10.2":
				rtt2filt.append(float(rtt.strip('\n')))
			else:
				rtt3filt.append(float(rtt.strip('\n')))
			if len(rtt2filt) == 5:
				rtt = sum(rtt2filt)/float(len(rtt2filt))
				rtt_dict[''+key+''] = rtt
				print "RTT value = ", rtt
				print "---------------------------------------"
				del rtt2filt[0]
			if len(rtt3filt) == 5:
				rtt = sum(rtt3filt)/float(len(rtt3filt))
				rtt_dict[''+key+''] = rtt
				print "RTT value = ", rtt
				print "---------------------------------------"
				del rtt3filt[0]
			
def handoff():
	global rtt_dict, cont_value, cont_dict
	old_controller = None
	cont_value = [2,2]
	while True:
		if len(rtt_dict) == 2 and len(cont_dict) == 2:
			if rtt_dict.values()[0] < rtt_dict.values()[1]:
				cont_value.append(2)
				del cont_value[0]
				new_controller = rtt_dict.keys()[0]
				if cont_value[0] == cont_value[1] and old_controller != new_controller:
					print "hand-off initiated"
					print "Controller set to %s" % rtt_dict.keys()[0]
					print "---------------------------------------"
					response = os.system("echo iist@123 | sudo ovs-vsctl set-controller br0 tcp:%s:6633 > /dev/null 2>&1" % str(rtt_dict.keys()[0]))
					old_controller = new_controller
			else:
				cont_value.append(4)
				del cont_value[0]
				new_controller = rtt_dict.keys()[1]
				if cont_value[0] == cont_value[1] and old_controller != new_controller:
					print "hand-off initiated"
					print "controller set to %s" % rtt_dict.keys()[1]
					print "---------------------------------------"
					response = os.system("echo iist@123 | sudo ovs-vsctl set-controller br0 tcp:%s:6633 > /dev/null 2>&1" % str(rtt_dict.keys()[1]))
					old_controller = new_controller
			
rad = threading.Thread(name='radio', target=radio)	
m = threading.Thread(name='mainfunction', target=mainfunction)
h = threading.Thread(name='handoff', target=handoff)

rad.start()
time.sleep(2)
m.start()
time.sleep(2)
h.start()
