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

__author__ = "Warodom Khamphanchai, Avijit Saha"
__credits__ = ""
__version__ = "1.2.1"
__maintainer__ = "Warodom Khamphanchai, Avijit Saha"
__email__ = "kwarodom@vt.edu, avijit@vt.edu"
__website__ = "kwarodom.wordpress.com"
__status__ = "Prototype"
__created__ = "2014-8-31 12:35:00"
__lastUpdated__ = "2015-02-11 22:18:40"
'''


'''This Dummy API class is for an dummy agent that want to communicate/monitor/control
devices that compatible with Radio Thermostat Wi-Fi USNAP Module'''

import urllib2 
import json
import time
import datetime
import random

class API:
    # 1. constructor : gets call every time when create a new class
    # requirements for instantiation 1. model, 2.type, 3.api, 4. address
    def __init__(self, **kwargs):  # default color is white
        # Initialized common attributes
        self.variables = kwargs
        self.set_variable('thermostat_mode', "HEAT")
        self.set_variable('fan_mode', "ON")
        self.set_variable('thermostat_state', "HEAT")
        self.set_variable('fan_state', "ON")
        self.set_variable('override', "override")
        self.set_variable('hold', "hold")
        self.set_variable('t_type_post', "t_type_post")
        _select_tmode = random.randint(0, 2)
        if _select_tmode == 0:
            self.set_variable('thermostat_mode', "OFF")
            self.set_variable('thermostat_state', "OFF")
        elif _select_tmode == 1:
            self.set_variable('thermostat_mode', "HEAT")
            self.set_variable('thermostat_state', "HEAT")
            self.set_variable('heat_setpoint', random.randint(65, 80))
        elif _select_tmode == 2:
            self.set_variable('thermostat_mode', "COOL")
            self.set_variable('thermostat_state', "COOL")
            self.set_variable('cool_setpoint', random.randint(65, 80))
        else:
            print("Invalid value for device thermostat_mode")
        _select_fmode = random.randint(0, 2)
        if _select_fmode == 0:
            self.set_variable('fan_mode', "AUTO")
            self.set_variable('fan_state', "OFF")
        elif _select_fmode == 1:
            self.set_variable('fan_mode', "CIRCULATE")
            self.set_variable('fan_state', "OFF")
        elif _select_fmode == 2:
            self.set_variable('fan_mode', "ON")
            self.set_variable('fan_state', "ON")
        else:
            print(" Invalid value for fan_mode")


    # These set and get methods allow scalability
    def set_variable(self, k, v): #k=key, v=value
        self.variables[k] = v

    def get_variable(self,k):
        return self.variables.get(k, None) # default of get_variable is none

    # 2. Attributes from Attributes table
    '''
    Attributes: 
    GET: temp, override, tstate, fstate, t_type_post
    GET/POST: time=[day, hour, minute], tmode, t_heat, t_cool, fmode, hold
    POST: energy_led 
    ------------------------------------------------------------------------------------------
    temp            GET              current temp(deg F)
    override        GET              target temp temporary override (0:disabled, 1:enabled) 
    tstate          GET              HVAC operating state (0:OFF,1:HEAT,2:COOL)
    fstate          GET              fan operating state (0:OFF, 1:ON)
    t_type_post
    time            GET    POST      Thermostat's internal time (day:int,hour:int,minute:int)
    tmode           GET    POST      Thermostat operating mode (0:OFF,1:HEAT,2:COOL,3:AUTO)
    t_heat          GET    POST      temporary target heat setpoint (floating point in deg F)
    t_cool          GET    POST      temporary target 
    .cool setpoint (floating point in deg F)
    fmode           GET    POST      fan operating mode (0:AUTO,1:AUTO/CIRCULATE,2:ON)
    hold            GET    POST      target temp hold status (0:disabled, 1:enabled)
    energy_led             POST      energy LED status code (0:OFF,1:Green,2:Yellow,4:Red) 
    ------------------------------------------------------------------------------------------ 
    ''' 

    # 3. Capabilites (methods) from Capabilities table
    '''
    API available methods:
    1. getDeviceStatus(url) GET
    2. setDeviceStatus(url, postmsg) POST
    3. identifyDevice(url, idenmsg) POST
    '''

    # method1: GET Open the URL and read the data
    def getDeviceStatus(self):
        print(" {0}Agent is querying its current status (status:200) please wait ...".format(self.variables.get('agent_id',None)))
        self.getDeviceStatusJson() #convert string data to JSON object then interpret it
        self.printDeviceStatus()

    def getDeviceStatusJson(self):
        self.set_variable('day', str(datetime.datetime.now().day))
        self.set_variable('hour', str(datetime.datetime.now().hour))
        self.set_variable('minute', str(datetime.datetime.now().minute))
        self.set_variable('temperature', random.randint(65, 80))

    def printDeviceStatus(self):
        print(" Day = {0} at {1}:{2}, the current status is as follows:"
              .format(self.get_variable('day'), self.get_variable('hour'), self.get_variable('minute')))
        print(" temperature = {}".format(self.get_variable('temperature')))
        print(" thermostat_mode = {}".format(self.get_variable('thermostat_mode')))
        if self.get_variable('thermostat_mode') == "HEAT":
            print(" heat_setpoint = {}".format(self.get_variable('heat_setpoint')))
        elif self.get_variable('thermostat_mode') == "COOL":
            print(" cool_setpoint = {}".format(self.get_variable('cool_setpoint')))
        print(" fan_mode = {}".format(self.get_variable('fan_mode')))
        print(" thermostat_state = {}".format(self.get_variable('thermostat_state')))
        print(" fan_state = {}".format(self.get_variable('fan_state')))

    # method2: POST Change thermostat parameters
    def setDeviceStatus(self, postmsg):
        setDeviceStatusResult = True
        for k, v in postmsg.items():
            self.set_variable(k, v)
        print("Radio Thermostat finished changing its status")
        return setDeviceStatusResult

    # method3: Identify this device (Physically)
    def identifyDevice(self):
        print("Radio Thermostat is identified")
        identifyDeviceResult = True
        return identifyDeviceResult

# This main method will not be executed when this class is used as a module
def main():
    # Step1: create an object with initialized data from DeviceDiscovery Agent
    # requirements for instantiation1. model, 2.type, 3.api, 4. address
    CT50Thermostat = API(model='CT50',agent_id='wifithermostat1', api='API1', address='http://38.68.232.64')
    print("{0}agent is initialzed for {1} using API={2} at {3}".format(CT50Thermostat.get_variable('agent_id'),CT50Thermostat.get_variable('model'),CT50Thermostat.get_variable('api'),CT50Thermostat.get_variable('address')))

    # Step2: acquire a device model number from the API
    # CT50Thermostat.getDeviceModel()

    # Step3: read current thermostat status
    CT50Thermostat.getDeviceStatus()

    # Step4: change device operating set points
    CT50Thermostat.setDeviceStatus({"thermostat_mode": "COOL", "cool_setpoint": 60})

    # Step5: read current thermostat status
    CT50Thermostat.getDeviceStatus()

    # Step6: thermostat identification
    CT50Thermostat.identifyDevice()

if __name__ == "__main__": main()