sudo mkdir -p /usr/local/etc/openvswtch
sudo rm /usr/local/etc/openvswitch/conf.db
cd openvswitch-2.3.1/ 
sudo ovsdb-tool create /usr/local/etc/openvswitch/conf.db vswitchd/vswitch.ovsschema 
sudo ovsdb-server --remote=punix:/usr/local/var/run/openvswitch/db.sock --remote=db:Open_vSwitch,Open_vSwitch,manager_options --pidfile --detach 
sudo ovs-vsctl --no-wait init 
sudo ovs-vswitchd --pidfile --detach 


sudo ovs-vsctl del-br br0 
sudo ovs-vsctl add-br br0 -- set Bridge br0 fail-mode=secure 

sudo ovs-vsctl set bridge br0 other-config:datapath-id=0000000000000005 
sudo ovs-vsctl add-port br0 wlan0
sudo ifconfig wlan0 0
sudo ifconfig br0 10.10.10.5 netmask 255.255.0.0 up
sudo route add default gw 10.10.1.1 br0
sudo ovs-vsctl set-controller br0 tcp:10.10.10.2:6633 tcp:10.10.10.3:6633

