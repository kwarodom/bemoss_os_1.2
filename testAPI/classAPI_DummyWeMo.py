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

__author__ = "Avijit Saha, Warodom Khamphanchai"
__credits__ = ""
__version__ = "1.2.1"
__maintainer__ = "Avijit Saha, Warodom Khamphanchai"
__email__ = "avijit@vt.edu, kwarodom@vt.edu"
__website__ = "kwarodom.wordpress.com"
__status__ = "Prototype"
__created__ = "2014-8-29 17:15:00"
__lastUpdated__ = "2015-02-11 22:22:33"
'''

'''This APIclass is for an agent that want to communicate/monitor/control
devices that compatible with WeMo API'''

import os
import re
import urllib2
import requests
from xml.dom import minidom
import time
import json
import random

class API:
    # 1. constructor : gets call everytime when create a new class
    # requirements for instantiation1. model, 2.type, 3.api, 4. address
    def __init__(self,**kwargs): #default color is white
        # Initialized common attributes
        self.variables = kwargs
        _select_status = random.randint(1, 2)
        if _select_status == 1:
               self.set_variable('status', "ON")
        else:
               self.set_variable('status', "OFF")
       
    # These set and get methods allow scalability
    def set_variable(self,k,v):  # k=key, v=value
        self.variables[k] = v

    def get_variable(self,k):
        return self.variables.get(k, None) #default of get_variable is none

    # 2. Attributes from Attributes table
    '''
    Attributes:
    Status     GET/POST   Current Device Status 1 or True for ON and  0 or False for OFF
    '''

    # 3. Capabilites (methods) from Capabilities table
    '''
    API available methods:
    1. getDeviceStatus() GET
    2. setDeviceStatus(newstatus) POST
    3. identifyDevice() POST
    '''    

    # method1: GET device status by XML read
    def getDeviceStatus(self):
        print(" {0}Agent is querying its current status please wait ...".format(self.variables.get('agent_id',None)))
        self.printDeviceStatus()

    def printDeviceStatus(self):
        print(" The current Wemo status is as follows:")
        print(" status = {}".format(self.get_variable('status')))

    # method2: POST Change status
    def setDeviceStatus(self, newstatus):
        setDeviceStatusResult = True

        _data = json.dumps(newstatus)
        _data = json.loads(_data)

        if _data['status'] == "OFF":
            self.set_variable('status',"OFF")
        elif _data['status'] == "ON":
            self.set_variable('status',"ON")

        return setDeviceStatusResult
            
    # method3: Identify Device by Toggling device status twice
    def identifyDevice(self):
        identifyDeviceResult = False
        try:
            self.getDeviceStatus()
            self.toggleDeviceStatus()
            print(self.get_variable("model")+" is being identified with starting status "+str(self.get_variable('status')))
            self.timeDelay(5)
            self.toggleDeviceStatus()
            print("Identification for "+self.get_variable("model")+" is done with status "+str(self.get_variable('status')))
            identifyDeviceResult = True
        except:
            print("ERROR: classAPI_WeMo connection failure! @ identifyDevice")
        return identifyDeviceResult

    # ------------ Helper Methods -------------------------------------
    # method4: GET current status and POST toggled status
    def toggleDeviceStatus(self):
        if self.get_variable('status') == "ON":
            self.setDeviceStatus({"status":"OFF"})
        else:
            self.setDeviceStatus({"status":"ON"})

    # method5: time delay
    def timeDelay(self,time_iden): #specify time_iden for how long to delay the process
        t0 = time.time()
        self.seconds = time_iden
        while time.time() - t0 <= time_iden:
            self.seconds = self.seconds - 1
            print("wait: {} sec".format(self.seconds))
            time.sleep(1)
    # -----------------------------------------------------------------


# This main method will not be executed when this class is used as a module
def main():
    # First create an object with initialized data from DeviceDiscovery Agent
    # requirements for instantiation1. model, 2.type, 3.api, 4. address
    WeMoSwitch = API(model='WeMo',type='WiFiplug',api='classAPI_WeMo',address='http://38.68.232.156:49153')
    WeMoSwitch.getDeviceStatus()
    # Set Device Status by True/False Argument
    WeMoSwitch.setDeviceStatus({"status": "OFF"})
    WeMoSwitch.getDeviceStatus()
    WeMoSwitch.setDeviceStatus({"status": "ON"})
    WeMoSwitch.getDeviceStatus()

if __name__ == "__main__": main()