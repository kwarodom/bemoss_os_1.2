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
__lastUpdated__ = "2015-02-11 22:16:33"
'''

import time
import urllib2
import json
import random
from colormath.color_objects import sRGBColor, xyYColor
from colormath.color_conversions import convert_color

class API:
    # 1. constructor : gets call every time when create a new class
    # requirements for instantiation1. model, 2.type, 3.api, 4. address
    def __init__(self,**kwargs):  # default color is white
        # Initialized common attributes
        self.variables = kwargs
        _select_status = random.randint(1, 2)
        if _select_status == 1:
               self.set_variable('status', "ON")
        else:
               self.set_variable('status', "OFF")
        self.set_variable('brightness',random.randint(10, 100))
        self.set_variable('color',(random.randint(10, 255),random.randint(10, 255),random.randint(10, 255)))
        self.set_variable('number_lights', random.randint(1, 3))
        self.set_variable('effect',"none")
        self.set_variable('colormode',"xy")
        self.set_variable('hue',random.randint(1, 65535))
        self.set_variable('saturation',random.randint(10, 100))

    # These set and get methods allow scalability
    def set_variable(self,k,v): #k=key, v=value
        self.variables[k] = v

    def get_variable(self,k):
        return self.variables.get(k, None) #default of get_variable is none

    # 2. Attributes from Attributes table
    '''
    Attributes: 
    ''' 

    # 3. Capabilites (methods) from Capabilities table
    '''
    API3 available methods:
    1. getDeviceStatus() GET
    2. setDeviceStatus(postmsg) PUT
    3. identifyDevice()
    '''
    
    #----------------------------------------------------------------------
    # method1: getDeviceStatus()
    def getDeviceStatus(self):
        print(" {0}Agent is querying its current status (status:200) please wait ...".
                  format(self.variables.get('agent_id', None)))
        self.printDeviceStatus()
        
    def printDeviceStatus(self):
        # now we can access the contents of the JSON like any other Python object
        print(" the current status is as follows:")
        #print(" name = {}".format(self.get_variable('name')))
        print(" number_lights = {}".format(self.get_variable('number_lights')))
        print(" status = {}".format(self.get_variable('status')))
        print(" brightness = {}".format(self.get_variable('brightness')))
        print(" hue = {}".format(self.get_variable('hue')))
        print(" color = {}".format(self.get_variable('color')))
        print(" saturation = {}".format(self.get_variable('saturation')))
        #print(" xy= {}".format(self.get_variable('xy')))
        #print(" ct = {}".format(self.get_variable('ct')))
        print(" effect = {}".format(self.get_variable('effect')))
        print(" colormode = {}\n".format(self.get_variable('colormode')))
    #----------------------------------------------------------------------

    #----------------------------------------------------------------------
    # method2: setDeviceStatus(postmsg)
    def setDeviceStatus(self, postmsg):
        setDeviceStatusResult = True
        for k, v in postmsg.items():
            self.set_variable(k, v)
        print ("{}Agent changed Philips Hue status successfully".format(self.variables.get('agent_id', None)))
        return setDeviceStatusResult

    #----------------------------------------------------------------------
    # method3: Identify this lights (Physically)
    def identifyDevice(self):
        identifyDeviceResult = False
        print(" {0}Agent for {1} is identifying itself by doing colorloop. Please observe your lights"
              .format(self.variables.get('agent_id',None), self.variables.get('model',None)))
        try:
            devicewasoff=0
            if self.get_variable('status')=="OFF":
                devicewasoff=1
                self.setDeviceStatus({"status":"ON"})
            self.setDeviceStatus({"effect": "colorloop"})
            time_iden = 10 #time to do identification
            t0 = time.time()
            self.seconds = time_iden
            while time.time() - t0 <= time_iden:
                self.seconds = self.seconds - 1
                print("wait: {} sec".format(self.seconds))
                time.sleep(1)
            self.setDeviceStatus({"effect": "none"})
            if devicewasoff==1:
                self.setDeviceStatus({"status":"OFF"})
            identifyDeviceResult = True
        except:
            print("ERROR: classAPI_DummyPhilipsHue connection failure! @ identifyDevice")
        return identifyDeviceResult
    # ----------------------------------------------------------------------

# This main method will not be executed when this class is used as a module
def main():
    # Step1: create an object with initialized data from DeviceDiscovery Agent
    # requirements for instantiation1. model, 2.type, 3.api, 4. address
    PhilipsHue = API(model='Philips Hue',type='wifiLight',api='API3',address='http://38.68.232.24/api/newdeveloper/groups/0/', agent_id='WifiThermostat1')
    print("{0}agent is initialzed for {1} using API={2} at {3}".format(PhilipsHue.get_variable('type'),PhilipsHue.get_variable('model'),PhilipsHue.get_variable('api'),PhilipsHue.get_variable('address')))

    PhilipsHue.getDeviceStatus()
    PhilipsHue.setDeviceStatus({"status":"ON","color":(55,13,255)})

    PhilipsHue.getDeviceStatus()
    print PhilipsHue.variables

if __name__ == "__main__": main()