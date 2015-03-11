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
#__lastUpdated__ = "2015-02-11 21:53:29"

sudo chmod 777 -R ~/.config/volttron/
sudo rm ~/.config/volttron/lite/agents/*
sudo chmod 777 -R ~/workspace
cd ~/workspace/bemoss_os/
sudo bin/volttron-lite -c dev-config.ini -v -v &
cd ~/workspace/bemoss_os
sudo rm Agents/devicediscoveryagent-0.1-py2.7.egg
sudo rm bin/devicediscoveryagent-0.1-py2.7.egg
sudo volttron/scripts/build-agent.sh DeviceDiscoveryAgent
sudo bin/volttron-ctrl install-executable Agents/devicediscoveryagent-0.1-py2.7.egg
sudo rm Agents/listeneragent-0.1-py2.7.egg
sudo rm bin/listeneragent-0.1-py2.7.egg
sudo volttron/scripts/build-agent.sh ListenerAgent
sudo bin/volttron-ctrl install-executable Agents/listeneragent-0.1-py2.7.egg
sudo rm Agents/thermostatagent-0.1-py2.7.egg
sudo rm bin/thermostatagent-0.1-py2.7.egg
sudo volttron/scripts/build-agent.sh ThermostatAgent
sudo bin/volttron-ctrl install-executable Agents/thermostatagent-0.1-py2.7.egg
sudo rm Agents/plugloadagent-0.1-py2.7.egg
sudo rm bin/plugloadagent-0.1-py2.7.egg
sudo volttron/scripts/build-agent.sh PlugloadAgent
sudo bin/volttron-ctrl install-executable Agents/plugloadagent-0.1-py2.7.egg
sudo rm Agents/lightingagent-0.1-py2.7.egg
sudo rm bin/lightingagent-0.1-py2.7.egg
sudo volttron/scripts/build-agent.sh LightingAgent
sudo bin/volttron-ctrl install-executable Agents/lightingagent-0.1-py2.7.egg
