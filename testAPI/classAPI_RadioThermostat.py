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
__created__ = "2014-6-26 09:12:00"
__lastUpdated__ = "2015-02-11 22:29:53"
'''

'''This API class is for an agent that want to communicate/monitor/control
devices that compatible with Radio Thermostat Wi-Fi USNAP Module API Version 1.3 March 22, 2012
http://www.radiothermostat.com/documents/rtcoawifiapiv1_3.pdf'''

import urllib2 
import json
import time

class API:
    # 1. constructor : gets call every time when create a new class
    # requirements for instantiation1. model, 2.type, 3.api, 4. address
    def __init__(self,**kwargs):  # default color is white
        # Initialized common attributes
        self.variables = kwargs

    # These set and get methods allow scalability
    def set_variable(self,k,v):  # k=key, v=value
        self.variables[k] = v

    def get_variable(self,k):
        return self.variables.get(k, None)  #  default of get_variable is none

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
    API1 available methods:
    1. getDeviceModel(url) GET
    2. getDeviceStatus(url) GET
    3. setDeviceStatus(url, postmsg) POST
    4. identifyDevice(url, idenmsg) POST
    '''    
    # method1: GET Open the URL and obtain a model number of a device
    def getDeviceModel(self):
        _urlData = self.get_variable("address")
        print _urlData
        try:
            _deviceModelUrl = urllib2.urlopen(_urlData+"/tstat/model")  # without data argument this is a GET command
            print(" {0}Agent is querying a model number (status:{1}) please wait ...".format(self.variables.get('agent_id',None), _deviceModelUrl.getcode()))
            if _deviceModelUrl.getcode() == 200:
                _deviceModel = self.getDeviceModelJson(_deviceModelUrl.read().decode("utf-8"))
                self.set_variable("deviceModel", _deviceModel)
                print(" {} model is {}\n".format(self.variables.get('agent_id', None), self.get_variable("deviceModel")))
            else:
                print(" wrong url for getting a device model number\n")
        except:
            print("Connection to {0}:{1} failed".format(self.get_variable("agent_id"),self.get_variable("model")))

    def getDeviceModelJson(self,data):
        _theJSON = json.loads(data)
        self.set_variable("deviceModel", _theJSON["model"])
        return _theJSON["model"]

    # method2: GET Open the URL and read the data
    def getDeviceStatus(self):
        _urlData = self.get_variable("address")+'/tstat'
        _deviceUrl = urllib2.urlopen(_urlData)
        print(" {0}Agent is querying its current status (status:{1}) please wait ...".format(self.variables.get('agent_id',None), _deviceUrl.getcode()))
        if (_deviceUrl.getcode() == 200): #200 means data is get successfully
            #currentstatus = self.getDeviceStatusJson(deviceUrl.read().decode("utf-8"))
            self.getDeviceStatusJson(_deviceUrl.read().decode("utf-8"))  # convert string data to JSON object
            self.printDeviceStatus()
        else:
            print (" Received an error from server, cannot retrieve results " + str(_deviceUrl.getcode()))

    def getDeviceStatusJson(self, data):
        # Use the json module to load the string data into a dictionary
        _theJSON = json.loads(data)
        self.set_variable('day',_theJSON["time"]["day"])   
        self.set_variable('hour',_theJSON["time"]["hour"])   
        self.set_variable('minute',_theJSON["time"]["minute"])
        self.set_variable('override',_theJSON["override"])
        self.set_variable('hold',_theJSON["hold"])
        self.set_variable('t_type_post',_theJSON["t_type_post"])
        # now we can access the contents of the JSON like any other Python object
        # 1. temperature
        if _theJSON["temp"] == -1:
            pass
        else:
            self.set_variable('temperature',_theJSON["temp"])
        # 2. thermostat_mode
        if _theJSON["tmode"] == 0:
            self.set_variable('thermostat_mode', "OFF")
        elif _theJSON["tmode"] == 1:
            self.set_variable('thermostat_mode', "HEAT")
            self.set_variable('heat_setpoint',_theJSON["t_heat"])
        elif _theJSON["tmode"] == 2:
            self.set_variable('thermostat_mode', "COOL")
            self.set_variable('cool_setpoint',_theJSON["t_cool"])
        elif _theJSON["tmode"] == 3:
            self.set_variable('thermostat_mode', "AUTO")
        else: 
            print("Invalid value for device thermostat_mode")
        # 3. fan_mode
        if _theJSON["fmode"] == 0:
            self.set_variable('fan_mode', "AUTO")
        elif _theJSON["fmode"] == 1:
            self.set_variable('fan_mode', "CIRCULATE")
        elif _theJSON["fmode"] == 2:
            self.set_variable('fan_mode', "ON")
        else:
            print(" Invalid value for fan_mode")
        # 4. thermostat_state
        if _theJSON["tstate"] == 0:
            self.set_variable('thermostat_state', "OFF")
        elif _theJSON["tstate"] == 1:
            self.set_variable('thermostat_state', "HEAT")
        elif _theJSON["tstate"] == 2:
            self.set_variable('thermostat_state', "COOL")
        else:
            print(" Invalid value for thermostat_state")
        # 5. fan_state
        if _theJSON["fstate"] == 0:
            self.set_variable('fan_state', "OFF")
        elif _theJSON["fstate"] == 1:
            self.set_variable('fan_state', "ON")
        else:
            print(" Invalid value for fan_state")
        # return _theJSON["model"]

    def printDeviceStatus(self):
        print(" Day = {0} at {1}:{2}, the current status is as follows:".format(self.get_variable('day'),self.get_variable('hour'),self.get_variable('minute')))
        # 1. temperature
        print(" temperature = {}".format(self.get_variable('temperature')))
        print(" thermostat_mode = {}".format(self.get_variable('thermostat_mode')))
        if self.get_variable('thermostat_mode') == "HEAT":
            print(" heat_setpoint = {}".format(self.get_variable('heat_setpoint')))
        elif self.get_variable('thermostat_mode') == "COOL":
            print(" cool_setpoint = {}".format(self.get_variable('cool_setpoint')))
        print(" fan_mode = {}".format(self.get_variable('fan_mode')))
        print(" thermostat_state = {}".format(self.get_variable('thermostat_state')))
        print(" fan_state = {}".format(self.get_variable('fan_state')))
        # print(" override = {}".format(self.get_variable('override')))
        # print(" hold = {}".format(self.get_variable('hold')))
        # print(" t_type_post = {}\n".format(self.get_variable('t_type_post')))

    # method3: POST Change thermostat parameters
    def setDeviceStatus(self, postmsg):
        setDeviceStatusResult = True
        # Ex. postmsg = {"tmode":1,"t_heat":85})
        # Ex. postmsg = {"thermostatmode":"HEAT","heat_setpoint":85})
        # step1: parse postmsg
        _urlData = self.get_variable("address")+'/tstat'
        # step2: send message to change status of the device
        if self.isPostmsgValid(postmsg) == True:  # check if the data is valid
            _data = json.dumps(self.convertPostMsg(postmsg))
            _data = _data.encode(encoding='utf_8')
            _request = urllib2.Request(_urlData)
            _request.add_header('Content-Type','application/json')
            try:
                _f = urllib2.urlopen(_request, _data)  # when include data this become a POST command
                print(" {0}Agent for {1} is changing its status with {2} please wait ...".format(self.variables.get('agent_id',None),
                                                                                             self.variables.get('model',None),
                                                                                             self.convertPostMsg(postmsg)))
            except:
                setDeviceStatusResult = False
            print(" after send a POST request: {}".format(_f.read().decode('utf-8')))
        else:
            print("The POST message is invalid, check thermostat_mode, heat_setpoint, cool_coolsetpoint setting and try again\n")
        return setDeviceStatusResult

    def isPostmsgValid(self,postmsg):  # check validity of postmsg
        dataValidity = True
        for k,v in postmsg.items():
            if k == 'thermostat_mode':
                if postmsg.get('thermostat_mode') == "HEAT":
                    for k,v in postmsg.items():
                        if k == 'cool_setpoint':
                            dataValidity = False
                            break
                elif postmsg.get('thermostat_mode') == "COOL":
                    for k,v in postmsg.items():
                        if k == 'heat_setpoint':
                            dataValidity = False
                            break
        return dataValidity

    def convertPostMsg(self, postmsg):
        if 'thermostat_mode' not in postmsg:
            if 'heat_setpoint' in postmsg:
                # self.set_variable("tmode",1)
                self.set_variable("t_heat",postmsg.get("heat_setpoint"))
                # msgToDevice = {"tmode":self.get_variable("tmode"),"t_heat":self.get_variable("t_heat")}
                msgToDevice = {"t_heat":self.get_variable("t_heat")}
            elif 'cool_setpoint' in postmsg:
                # self.set_variable("tmode",2)
                self.set_variable("t_cool",postmsg.get("cool_setpoint"))
                # msgToDevice = {"tmode":self.get_variable("tmode"),"t_cool":self.get_variable("t_cool")}
                msgToDevice = {"t_cool":self.get_variable("t_cool")}
            else: pass
        else: pass
        for k,v in postmsg.items():
            if k == 'thermostat_mode':
                if postmsg.get('thermostat_mode') == "HEAT":
                    self.set_variable("tmode",1)
                    self.set_variable("t_heat",postmsg.get("heat_setpoint"))
                    msgToDevice = {"tmode":self.get_variable("tmode"),"t_heat":self.get_variable("t_heat")}
                elif postmsg.get('thermostat_mode') == "COOL":
                    self.set_variable("tmode",2)
                    self.set_variable("t_cool",postmsg.get("cool_setpoint"))
                    msgToDevice = {"tmode":self.get_variable("tmode"),"t_cool":self.get_variable("t_cool")}
                elif postmsg.get('thermostat_mode') == "OFF":
                    self.set_variable("tmode",0)
                    msgToDevice = {"tmode":self.get_variable("tmode")}
                elif postmsg.get('thermostat_mode') == "AUTO":
                    self.set_variable("tmode",3)
                    msgToDevice = {"tmode":self.get_variable("tmode")}
                else:
                    msgToDevice = {}
            if k == 'fan_mode':
                if postmsg.get('fan_mode') == "AUTO":
                    msgToDevice['fmode']=0
                elif postmsg.get('fan_mode') == "CIRCULATE":
                    msgToDevice['fmode']=1
                elif postmsg.get('fan_mode') == "ON":
                    msgToDevice['fmode']=2
                else:
                    print("invalid argument for fan_mode")
            if k == 'thermostat_state':
                if postmsg.get('thermostat_state') == "OFF":
                    msgToDevice['tstate']=0
                elif postmsg.get('thermostat_state') == "HEAT":
                    msgToDevice['tstate']=1
                elif postmsg.get('thermostat_state') == "COOL":
                    msgToDevice['tstate']=2
                else:
                    print("invalid argument for thermostat_state")
            if k == 'fan_state':
                if postmsg.get('fan_state') == "OFF":
                    msgToDevice['fstate']=0
                elif postmsg.get('fan_state') == "ON":
                    msgToDevice['fstate']=1
                else:
                    print("invalid argument for fan_state")
        return msgToDevice

    # method4: Identify this device (Physically)
    def identifyDevice(self):
        identifyDeviceResult = False
        _data = json.dumps({'energy_led': 2})
        _data = _data.encode(encoding='utf_8')
        _request = urllib2.Request(self.get_variable('address')+"/tstat/led")
        _request.add_header('Content-Type','application/json')
        try:
            _f = urllib2.urlopen(_request, _data) #when include data this become a POST command
            print(" after send a POST request: {}".format(_f.read().decode('utf-8')))
        except:
            print("ERROR: classAPI_RadioThermostat connection failure! @ identifyDevice")
        print(" {0}Agent for {1} is identifying itself by changing LED light to yellow for 10 seconds "
              "then back to green please wait ...".format(self.variables.get('device_type', None),
                                                          self.variables.get('model', None)))
        _data = json.dumps({'energy_led': 1})
        _data = _data.encode(encoding='utf_8')
        _request = urllib2.Request(self.get_variable('address')+"/tstat/led")
        _request.add_header('Content-Type','application/json')
        try:
            self.timeDelay(10)
            _f = urllib2.urlopen(_request, _data) #when include data this become a POST command
            print(" after send a POST request: {}".format(_f.read().decode('utf-8')))
            identifyDeviceResult = True
        except:
            print("ERROR: classAPI_RadioThermostat connection failure! @ identifyDevice")
        return identifyDeviceResult

    # method5: time delay
    def timeDelay(self,time_iden): #specify time_iden for how long to delay the process
        t0 = time.time()
        self.seconds = time_iden
        while time.time() - t0 <= time_iden:
            self.seconds = self.seconds - 1
            print("wait: {} sec".format(self.seconds))
            time.sleep(1)

# This main method will not be executed when this class is used as a module
def main():
    # Step1: create an object with initialized data from DeviceDiscovery Agent
    # requirements for instantiation1. model, 2.type, 3.api, 4. address
    CT50Thermostat = API(model='CT50',agent_id='wifithermostat1',api='API1',address='http://38.68.232.64')
    print("{0}agent is initialzed for {1} using API={2} at {3}".format(CT50Thermostat.get_variable('agent_id'),CT50Thermostat.get_variable('model'),CT50Thermostat.get_variable('api'),CT50Thermostat.get_variable('address')))
    # Step2: acquire a device model number from the API
    CT50Thermostat.getDeviceModel()
    # Step3: read current thermostat status
    CT50Thermostat.getDeviceStatus()
    # postmsg = {"thermostat_mode":"COOL","cool_setpoint":60,"thermostat_state":"OFF","fan_state":"ON"}
    # print(CT50Thermostat.isPostmsgValid(postmsg))
    # Step4: change device operating set points
    CT50Thermostat.setDeviceStatus({"thermostat_mode":"HEAT","heat_setpoint":76})
    # Step5: read current thermostat status
    CT50Thermostat.getDeviceStatus()
    # Step6: thermostat identification
    # CT50Thermostat.identifyDevice()

if __name__ == "__main__": main()