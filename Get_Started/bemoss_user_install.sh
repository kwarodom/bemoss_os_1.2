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

#__author__ = "Warodom Khamphanchai, Avijit Saha"
#__credits__ = ""
#__version__ = "1.2.1"
#__maintainer__ = "Warodom Khamphanchai, Avijit Saha"
#__email__ = "kwarodom@vt.edu, avijit@vt.edu"
#__website__ = "kwarodom.wordpress.com"
#__status__ = "Prototype"
#__created__ = "2014-09-12 12:04:50"
#__lastUpdated__ = "2015-02-12 13:48:32"

#Download the package lists from the repositories and update them
sudo apt-get update
#Download and install the dependencies of the BEMOSS platform
sudo apt-get install g++ mercurial python-dev libevent-dev libssl-dev python-pip libffi-dev libpq-dev python-tk python-psycopg2 python-zmq --assume-yes
sudo pip install netifaces networkx
sudo mkdir ~/workspace
#Remove the existing bemoss_os folder
sudo rm -rf ~/workspace/bemoss_os
sudo rm -rf ~/workspace/bemoss_os_v1.2
sudo rm -rf ~/workspace/bemoss_os_v1.2.1
#Clone the bemoss_os repository
cd ~/workspace
sudo hg clone https://bitbucket.org/bemoss/bemoss_os_v1.2.1
#Change repo name from v1.2
sudo mv ~/workspace/bemoss_os_v1.2.1 ~/workspace/bemoss_os
sudo rm -rf ~/workspace/bemoss_os_v1.2.1
#Compile dependency codes in C/C++
cd ~/workspace
sudo chmod 777 -R bemoss_os
#Go to the bemoss_os folder and run the bootstrap command
cd ~/workspace/bemoss_os
sudo ./bootstrap
#Remove colormath egg files and copy to the /bemoss_os/eggs folder
sudo rm -rf ~/workspace/bemoss_os/eggs/colormath-2.0.2-py2.7.egg
sudo cp -a ~/workspace/bemoss_os/bemoss/custom-eggs/colormath-2.0.2-py2.7.egg ~/workspace/bemoss_os/eggs
#Download and install the dependencies for web_UI
sudo pip install django==1.4
sudo pip install tornado
sudo pip install six
sudo pip install pyzmq --upgrade --install-option="--zmq=bundled"
sudo ldconfig
#Download and install the dependencies of the postgresql database
sudo apt-get install postgresql postgresql-contrib python-yaml --assume-yes
cd ~/workspace
#Remove the existing bemoss_web_ui folder
sudo rm -rf bemoss_web_ui
sudo rm -rf bemoss_web_ui_v2
#Clone the bemoss_web_ui repository
sudo hg clone https://bitbucket.org/bemoss/bemoss_web_ui_v1.2.1
#Change repo name from v2
sudo mv ~/workspace/bemoss_web_ui_v1.2.1 ~/workspace/bemoss_web_ui
sudo rm -rf bemoss_web_ui_v1.2.1
sudo rm -rf bemoss_web_ui_v1.2
#Give the full permission to access the workspace folder
sudo chmod 777 -R ~/workspace
#Create the bemossdb database
sudo -u postgres psql -c "CREATE USER admin WITH PASSWORD 'admin';"
sudo -u postgres psql -c "DROP DATABASE IF EXISTS bemossdb;"
sudo -u postgres createdb bemossdb -O admin
sudo -u postgres psql -d bemossdb -c "create extension hstore;"
#Install the dependencies of the sMAP database and create archiever database
yes ""| sudo add-apt-repository ppa:stevedh/smap
sudo apt-get update
sudo apt-get install readingdb readingdb-python python-smap powerdb2 monit --assume-yes
sudo pip install tablib
VAR=$(sudo wc -l < /etc/monit/monitrc)
if [ $VAR = 248 ]; then
	echo "  set httpd port 2812 and\r\n     use address localhost\r\n     allow localhost"  >> /etc/monit/monitrc
fi
sudo /etc/init.d/monit restart
sudo a2dissite default
sudo a2ensite powerdb2
sudo service apache2 reload
sudo -u postgres psql -d archiver -c "create extension hstore;"
sudo -u postgres psql -d archiver -c "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO admin;"
sudo cp -a /usr/share/powerdb2 /usr/lib/python2.7/dist-packages
#Go to the bemoss_web_ui and run the syncdb command for the database tables (ref: model.py)
sudo python ~/workspace/bemoss_web_ui/manage.py syncdb
sudo python ~/workspace/bemoss_web_ui/defaultDB.py
#Copy the volttron and egg folders to the system python folder
sudo cp -a ~/workspace/bemoss_os/volttron /usr/lib/python2.7/dist-packages
sudo cp -a ~/workspace/bemoss_os/eggs/pyzmq-14.3.1-py2.7-linux-i686.egg/zmq /usr/lib/python2.7/dist-packages
#Cross-check if volttron installed properly
if [ ! -f ~/workspace/bemoss_os/bin/python ] || [ ! -f ~/workspace/bemoss_os/bin/volttron-lite ]; then
	cd ~/workspace/bemoss_os
	sudo ./bootstrap
fi
#Go to bemoss/Applications folder to install Apps inclding AppLauncher and Pre-install Apps
echo "Installing BEMOSS Apps..."
cd ~/workspace/bemoss_os
sudo chmod 777 volttron.log
sudo rm volttron.log
sudo chmod 777 -R ~/workspace
cd ~/workspace/bemoss_os/bemoss/lite
sudo python platform_initiator_core.py
cd ~/workspace/bemoss_os/bemoss/Applications/code/AppLauncherAgent
sudo python installapp.py
cd ~/workspace/bemoss_os/bemoss/Applications/code/Thermostat_Scheduler
sudo python installapp.py
cd ~/workspace/bemoss_os/bemoss/Applications/code/Lighting_Scheduler
sudo python installapp.py
cd ~/workspace/bemoss_os/bemoss/Applications/code/Plugload_Scheduler
sudo python installapp.py
sleep 1
echo "BEMOSS App installation complete!"
cd ~/workspace/bemoss_os/runAgents
sudo ./buildAgents.sh
sudo killall volttron-lite
echo "BEMOSS Agents installation complete!"
#Prompt User to Reboot
echo "Installation Done! Please configure SMAP according to BEMOSS Wiki if you want to use SMAP."
echo "To finish BEMOSS installation you need to reboot. Do you want to reboot now (yes/no)?:"
read CHOICE
if [ "$CHOICE" = "yes" ] || [ "$CHOICE" = "y" ]; then
	sudo reboot
else
	echo "Reboot cancelled! Please manually reboot before using BEMOSS."
fi
