# -*- coding: utf-8 -*-
'''
Copyright © 2014 by Virginia Polytechnic Institute and State University
All rights reserved

Virginia Polytechnic Institute and State University (Virginia Tech) owns the copyright for the BEMOSS software and its
associated documentation (“Software”) and retains rights to grant research rights under patents related to
the BEMOSS software to other academic institutions or non-profit research institutions.
You should carefully read the following terms and conditions before using this software.
Your use of this Software indicates your acceptance of this license agreement and all terms and conditions.

You are hereby licensed to use the Software for Non-Commercial Purpose only.  Non-Commercial Purpose means the
use of the Software solely for research.  Non-Commercial Purpose excludes, without limitation, any use of
the Software, as part of, or in any way in connection with a product or service which is sold, offered for sale,
licensed, leased, loaned, or rented.  Permission to use, copy, modify, and distribute this compilation
for Non-Commercial Purpose to other academic institutions or non-profit research institutions is hereby granted
without fee, subject to the following terms of this license.

Commercial Use If you desire to use the software for profit-making or commercial purposes,
you agree to negotiate in good faith a license with Virginia Tech prior to such profit-making or commercial use.
Virginia Tech shall have no obligation to grant such license to you, and may grant exclusive or non-exclusive
licenses to others. You may contact the following by email to discuss commercial use: vtippatents@vtip.org

Limitation of Liability IN NO EVENT WILL VIRGINIA TECH, OR ANY OTHER PARTY WHO MAY MODIFY AND/OR REDISTRIBUTE
THE PROGRAM AS PERMITTED ABOVE, BE LIABLE TO YOU FOR DAMAGES, INCLUDING ANY GENERAL, SPECIAL, INCIDENTAL OR
CONSEQUENTIAL DAMAGES ARISING OUT OF THE USE OR INABILITY TO USE THE PROGRAM (INCLUDING BUT NOT LIMITED TO
LOSS OF DATA OR DATA BEING RENDERED INACCURATE OR LOSSES SUSTAINED BY YOU OR THIRD PARTIES OR A FAILURE
OF THE PROGRAM TO OPERATE WITH ANY OTHER PROGRAMS), EVEN IF VIRGINIA TECH OR OTHER PARTY HAS BEEN ADVISED
OF THE POSSIBILITY OF SUCH DAMAGES.

For full terms and conditions, please visit https://bitbucket.org/bemoss/bemoss_os.

Address all correspondence regarding this license to Virginia Tech’s electronic mail address: vtippatents@vtip.org

__author__ = "Warodom Khamphanchai"
__credits__ = ""
__version__ = "1.2.1"
__maintainer__ = "Warodom Khamphanchai"
__email__ = "kwarodom@vt.edu"
__website__ = "kwarodom.wordpress.com"
__status__ = "Prototype"
__created__ = "2014-8-29 17:15:00"
__lastUpdated__ = "2015-02-11 21:44:25"
'''

import os
import re
import sys
import time

# Keep Volttron Platform Alive Script ----------------------------------------------------------
# 1. check whether the platform is still running
print "Keep Platform Alive Agent >> check whether the platform is still running"
previous_working_directory = os.getcwd()
# print 'previous_working_directory' + previous_working_directory
os.chdir("../")  # = ~/workspace/bemoss_os
current_working_directory = os.getcwd()
# print 'current_working_directory' + current_working_directory
print os.getcwd()
sys.path.append(current_working_directory)

def keep_alive_platform():
    # print "Keep Platform Alive Agent >> check whether the platform is still running"
    os.system("sudo ps aux |grep volttron-lite > platform_status.txt")
    # 2. search for the platform process in platform_status.txt
    infile = open('platform_status.txt', 'r')
    platform_is_running = False
    for line in infile:
        # print(line, end='') #write to a next file name outfile
        match = re.search('bin/volttron-lite -c dev-config.ini -l volttron.log -v -v', line)
        if match:  # The platform process is running
            platform_is_running = True
        else:
            pass

    if platform_is_running is False:
        print "Keep Platform Alive Agent >> currently Volttron Platform is NOT running"
        print "Keep Platform Alive Agent >> restarting the platform"
        os.system("sudo bin/volttron-lite -c dev-config.ini -l volttron.log -v -v &")
        timeDelay(3)  # sleep for 3 sec before checking again
        # write time platform restart to text file
        os.system("sudo ~/workspace/bemoss_os/runAgents/runDeviceDiscoveryAgent.sh")
        print "Keep Platform Alive Agent >> DONE! restarting the platform"
    else:
        pass
        # print "Keep Platform Alive Agent >> Volttron Platform is running"

def timeDelay(time_iden):  # specify time_iden for how long to delay the process
    t0 = time.time()
    seconds = time_iden
    while time.time() - t0 <= time_iden:
        seconds = seconds - 1
        # print("Keep Platform Alive Agent >> wait: {} sec".format(seconds))
        time.sleep(1)

while True:
    # print 'Keep Platform Alive Agent >> current_working_directory' + os.getcwd()
    sys.path.append(current_working_directory)
    keep_alive_platform()
    timeDelay(60)  # sleep for 60 sec before checking again