#!/bin/sh
#Copyright © 2014 by Virginia Polytechnic Institute and State University
#All rights reserved

#Virginia Polytechnic Institute and State University (Virginia Tech) owns the copyright for the BEMOSS software and its
#associated documentation (“Software”) and retains rights to grant research rights under patents related to
#the BEMOSS software to other academic institutions or non-profit research institutions.
#You should carefully read the following terms and conditions before using this software.
#Your use of this Software indicates your acceptance of this license agreement and all terms and conditions.

#You are hereby licensed to use the Software for Non-Commercial Purpose only.  Non-Commercial Purpose means the
#use of the Software solely for research.  Non-Commercial Purpose excludes, without limitation, any use of
#the Software, as part of, or in any way in connection with a product or service which is sold, offered for sale,
#licensed, leased, loaned, or rented.  Permission to use, copy, modify, and distribute this compilation
#for Non-Commercial Purpose to other academic institutions or non-profit research institutions is hereby granted
#without fee, subject to the following terms of this license.

#Commercial Use If you desire to use the software for profit-making or commercial purposes,
#you agree to negotiate in good faith a license with Virginia Tech prior to such profit-making or commercial use.
#Virginia Tech shall have no obligation to grant such license to you, and may grant exclusive or non-exclusive
#licenses to others. You may contact the following by email to discuss commercial use: vtippatents@vtip.org

#Limitation of Liability IN NO EVENT WILL VIRGINIA TECH, OR ANY OTHER PARTY WHO MAY MODIFY AND/OR REDISTRIBUTE
#THE PROGRAM AS PERMITTED ABOVE, BE LIABLE TO YOU FOR DAMAGES, INCLUDING ANY GENERAL, SPECIAL, INCIDENTAL OR
#CONSEQUENTIAL DAMAGES ARISING OUT OF THE USE OR INABILITY TO USE THE PROGRAM (INCLUDING BUT NOT LIMITED TO
#LOSS OF DATA OR DATA BEING RENDERED INACCURATE OR LOSSES SUSTAINED BY YOU OR THIRD PARTIES OR A FAILURE
#OF THE PROGRAM TO OPERATE WITH ANY OTHER PROGRAMS), EVEN IF VIRGINIA TECH OR OTHER PARTY HAS BEEN ADVISED
#OF THE POSSIBILITY OF SUCH DAMAGES.

#For full terms and conditions, please visit https://bitbucket.org/bemoss/bemoss_os.

#Address all correspondence regarding this license to Virginia Tech’s electronic mail address: vtippatents@vtip.org

#__author__ = "Avijit Saha, Warodom Khamphanchai"
#__credits__ = ""
#__version__ = "1.2.1"
#__maintainer__ = "Avijit Saha, Warodom Khamphanchai"
#__email__ = "avijit@vt.edu, kwarodom@vt.edu"
#__website__ = "kwarodom.wordpress.com"
#__status__ = "Prototype"
#__created__ = "2014-09-12 12:04:50"
#__lastUpdated__ = "2015-02-11 22:12:48"

#Find own IP
sudo python ~/workspace/bemoss_os/bemoss/lite/find_own_ip.py
#Run Platform Initiator
sudo python ~/workspace/bemoss_os/bemoss/lite/platform_initiator_core.py
#Install Apps
cd ~/workspace/bemoss_os/bemoss/Applications/code/AppLauncherAgent
sudo python installapp.py
cd ~/workspace/bemoss_os/bemoss/Applications/code/Thermostat_Scheduler
sudo python installapp.py
cd ~/workspace/bemoss_os/bemoss/Applications/code/Lighting_Scheduler
sudo python installapp.py
cd ~/workspace/bemoss_os/bemoss/Applications/code/Plugload_Scheduler
sudo python installapp.py
sudo chmod 777 -R ~/workspace
#echo "BEMOSS App installation complete!"
#Configure webserver to run on own IP and Bind BACnet with IP
ipfile="${HOME}/workspace/bemoss_os/machine_ip.txt"
ipaddress=$(cat $ipfile)
case "$ipaddress" in
  *.*)
    webcommand="python bemoss_server.py --port=8000 --host=$ipaddress"
    export BACNET_IFACE=$ipaddress
    ;;
  *)
    webcommand="python bemoss_server.py --port=8000"
esac
#Run BEMOSS platform and Web Server
sudo gnome-terminal --tab -t "VolttronPlatform" -e "bash -c '~/workspace/bemoss_os/runAgents/runVolttronPlatform.sh'" --tab -t "MultiNode Server" -e "bash -c 'python ~/workspace/bemoss_os/bemoss/lite/udpserver.py'" --tab -t "ListenerAgent" -e "bash -c 'cd ~/workspace/bemoss_os/Agents; ~/workspace/bemoss_os/bin/python ListenerAgent/listener/agent.py -c ListenerAgent/listeneragent.launch.json -p ipc:///tmp/volttron-lite-agent-publish -s ipc:///tmp/volttron-lite-agent-subscribe'" --tab -t "keep_platform_alive" -e "bash -c 'python ~/workspace/bemoss_os/bemoss/lite/keep_platform_alive.py'" --tab -t "sMAP" -e "bash -c 'cd ~/workspace/bemoss_os; twistd -n smap smap_driver.ini'" --tab -t "IEBSubscriber" -e "bash -c 'cd ~/workspace/bemoss_web_ui; ~/workspace/bemoss_os/bin/python IEBSubscriber/iebsubscriber/agent.py -c IEBSubscriber/iebsubscriber.launch.json -p ipc:///tmp/volttron-lite-agent-publish -s ipc:///tmp/volttron-lite-agent-subscribe'" --tab -t "WebServer" -e "bash -c 'cd ~/workspace/bemoss_web_ui; $webcommand'" &
echo "BEMOSS platform run successfully!"
sudo echo $! > ~/workspace/bemoss_os/BEMOSS.pid
sleep 3
# Run Starter Agents
cd ~/workspace/bemoss_os
sudo bin/volttron-ctrl load-agent Agents/DeviceDiscoveryAgent/devicediscoveryagent.launch.json
sudo bin/volttron-ctrl start-agent devicediscoveryagent.launch.json
echo "BEMOSS Discovery Agent run successfully!"
sleep 2
sudo bin/volttron-ctrl load-agent bemoss/Applications/code/AppLauncherAgent/applauncheragent.launch.json
sudo bin/volttron-ctrl start-agent applauncheragent.launch.json
sudo bin/volttron-ctrl list-agent
echo "BEMOSS AppLauncher Agent run successfully!"
