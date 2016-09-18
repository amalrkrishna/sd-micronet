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
ett_dict = {}
etx_dict = {}
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

#Funtion to calculate the link bandwidth between the switch and the Controllers present in the network.
#Modified Packet pair method is implemented in this function. 
def bandwidth(ip_address,etx_value):
	global packetsize_avg
	print "bandwidth fuction called\n"
	probe_small = []
	probe_big = []
	probe_diff = []
	i = 0
	for i in range(0,2):
		probe_small.append(subprocess.check_output("ping -c 1 -s 137 " + ip_address + "| tail -1| awk '{print $4}' | cut -d '/' -f 2", shell=True))
		probe_big.append(subprocess.check_output("ping -c 1 -s 1137 " + ip_address + "| tail -1| awk '{print $4}' | cut -d '/' -f 2", shell=True))
		probe_small = [s.rstrip() for s in probe_small]
		probe_big = [s.rstrip() for s in probe_big]
		if (probe_big[i] != '') and (probe_small[i] != ''):
			probe_diff.append((float(probe_big[i])/2)+(float(probe_small[i])/2))
	probe_diff_min = min(probe_diff)
	bandwidth = float((1137*8*1000)/(probe_diff_min*1024*1024))
	return bandwidth

#The avergae packet size of packets transfered between the switch and the controllers is computed here.		
def packetsize(ip_address):
	global packetsize_avg
	print "packetsize function called\n"
	while True:
		packet = []
		os.system("echo iist@123 | sudo -S tcpdump -w capture.pcap -c 5 -i wlan0 host " + ip_address + "> /dev/null 2>&1")
		reader = pcapy.open_offline("capture.pcap")
		for i in range(0,4):
			(header, payload) = reader.next()
			packet.append(header.getlen())
		packetsize_avg = np.mean(packet)
		del packet
		return packetsize_avg
		time.sleep(0)

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
		etx = data_extracted[2]
		etx_dict[''+ip_address+''] = etx.strip('\0')
		
def rttcal(ip_address):
	rttcal = subprocess.check_output("ping -c 3 " + ip_address + "| tail -1| awk '{print $4}' | cut -d '/' -f 2", shell=True)
	return rttcal

def mainfunction():
	global ip_address, etx_dict, ett_dict, start_time, cont_value, cont_dict
	print "Main function started\n"
	
	while True:
		for key, value in cont_dict.iteritems():
			for key1, value1 in etx_dict.iteritems():
				if key == key1 and value1 != 'INFINITE':
					pkt = packetsize (key)
					bw = bandwidth (key, value1)
					rtt = rttcal (key)
					print "IP Address = ", key
					print "Average Packetsize = %f bytes" % pkt
					print "Bandwidth = %f Mbits/sec" % bw
					print "RTT = %f ms" % float(rtt)
					sb_ratio = float(pkt/bw)
					ett_value = float(value1)*float(sb_ratio)
					print "ETX value = ", value1
					print "ETT value = ", ett_value
					print "---------------------------------------"
					with open("test.txt", "a+") as myfile:
						myfile.write("%f, %s, %f, %f, %f, %f, %f, %d\n" % (float(time.time() - start_time),key,pkt,bw,float(value1), float(ett_value), float(rtt), cont_value))
					ett_dict[''+key+''] = ett_value
			
def handoff():
	global etx_dict, ett_dict, cont_value, cont_dict
	old_controller = None
	
	while True:
		if len(ett_dict) == 2:
			if ett_dict.values()[0] < ett_dict.values()[1]:
				new_controller = ett_dict.keys()[0]
				if old_controller != new_controller:
					print "hand-off initiated"
					print "Controller set to %s" % ett_dict.keys()[0]
					cont_value = 2
					print "---------------------------------------"
					response = os.system("echo iist@123 | sudo ovs-vsctl set-controller br0 tcp:%s:6633 > /dev/null 2>&1" % str(ett_dict.keys()[0]))
			else:
				new_controller = ett_dict.keys()[1]
				if old_controller != new_controller:
					print "hand-off initiated"
					print "controller set to %s" % ett_dict.keys()[1]
					cont_value = 4
					print "---------------------------------------"
					response = os.system("echo iist@123 | sudo ovs-vsctl set-controller br0 tcp:%s:6633 > /dev/null 2>&1" % str(ett_dict.keys()[1]))
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
