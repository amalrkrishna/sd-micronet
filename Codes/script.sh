sudo kill -9 `ps -ef | grep ovs | grep -v grep | awk '{print $2}'`
sudo modprobe openvswitch
sudo bash /home/amal/ovs.sh
sudo olsrd -d 1 &
#sleep 5
#sudo python sdn.py &
#sudo nping 10.10.10.4 --quiet --icmp --rate 100 -c 4000000000 &
#sudo nping 10.10.10.5 --quiet --icmp --rate 100 -c 4000000000 &
