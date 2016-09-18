import os
import subprocess
import time
import netifaces as ni
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt
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
cont_value = 0

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
			print "RTT = %f ms" % float(rtt)
			print "---------------------------------------"
			with open("test.txt", "a+") as myfile:
				myfile.write("%f, %s, %f, %d\n" % (float(time.time() - start_time),key,float(rtt), cont_value))
			rtt_dict[''+key+''] = rtt.strip('\n')
			
def handoff():
	global rtt_dict, cont_value
	old_controller = None
	
	while True:
		if len(rtt_dict) == 2:
			if rtt_dict.values()[0] < rtt_dict.values()[1]:
				new_controller = rtt_dict.keys()[0]
				if old_controller != new_controller:
					print "hand-off initiated"
					print "Controller set to %s" % rtt_dict.keys()[0]
					cont_value = 2
					print "---------------------------------------"
					response = os.system("echo iist@123 | sudo ovs-vsctl set-controller br0 tcp:%s:6633 > /dev/null 2>&1" % str(rtt_dict.keys()[0]))
			else:
				new_controller = rtt_dict.keys()[1]
				if old_controller != new_controller:
					print "hand-off initiated"
					print "controller set to %s" % rtt_dict.keys()[1]
					cont_value = 4
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
