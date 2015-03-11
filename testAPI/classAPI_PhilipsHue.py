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
__lastUpdated__ = "2015-02-11 22:25:03"
'''

import time
import urllib2
import json
from colormath.color_objects import sRGBColor, xyYColor
from colormath.color_conversions import convert_color

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
        return self.variables.get(k, None)  # default of get_variable is none

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

    # ----------------------------------------------------------------------
    # method1: getDeviceStatus(), getDeviceStatusJson(data), printDeviceStatus()
    def getDeviceStatus(self):
        _urlData = self.get_variable("address").replace(':80', '/api/newdeveloper/groups/0')
        try:
            _deviceUrl = urllib2.urlopen(_urlData)
            print(" {0}Agent is querying its current status (status:{1}) please wait ...".
                  format(self.variables.get('agent_id', None), _deviceUrl.getcode()))
            if (_deviceUrl.getcode() == 200): #200 means data is get successfully
                #currentstatus = self.getDeviceStatusJson(deviceUrl.read().decode("utf-8"))
                self.getDeviceStatusJson(_deviceUrl.read().decode("utf-8")) #convert string data to JSON object then interpret it
                self.printDeviceStatus()
            else:
                print (" Received an error from server, cannot retrieve results " + str(_deviceUrl.getcode()))
        except:
            print('ERROR: classAPI_PhilipsHue failed to getDeviceStatus')

    def getDeviceStatusJson(self,data):  
        # Use the json module to load the string data into a dictionary
        _theJSON = json.loads(data)
        # 1. status
        if _theJSON["action"]["on"] == True:
            self.set_variable('status',"ON")
        else:
            self.set_variable('status',"OFF")
        # 2. brightness convert to %
        self.set_variable('brightness',int(round(float(_theJSON["action"]["bri"])*100/255,0)))
        # 3. color convert to RGB 0-255
        self.set_variable('hue', _theJSON["action"]["hue"])
        self.set_variable('xy', _theJSON["action"]["xy"])
        self.set_variable('ct', _theJSON["action"]["ct"])
        self.set_variable('color', self.convertcolorxyYtoRGB(self.get_variable('xy'),float(_theJSON["action"]["bri"])/255))
        # 4. saturation convert to %
        self.set_variable('saturation',int(round(float(_theJSON["action"]["sat"])*100/255,0)))
        self.set_variable('effect',_theJSON["action"]["effect"])
        self.set_variable('colormode',_theJSON["action"]["colormode"])
        for k in _theJSON["lights"]:
            self.set_variable("lights{}".format(k), k)
        self.set_variable('number_lights', len(_theJSON["lights"]))
        self.set_variable('name',_theJSON["name"])
        
    def printDeviceStatus(self):
        # now we can access the contents of the JSON like any other Python object
        print(" the current status is as follows:")
        print(" name = {}".format(self.get_variable('name')))
        print(" number_lights = {}".format(self.get_variable('number_lights')))
        print(" status = {}".format(self.get_variable('status')))
        print(" brightness = {}".format(self.get_variable('brightness')))
        print(" hue = {}".format(self.get_variable('hue')))
        print(" color = {}".format(self.get_variable('color')))
        print(" saturation = {}".format(self.get_variable('saturation')))
        print(" xy= {}".format(self.get_variable('xy')))
        print(" ct = {}".format(self.get_variable('ct')))
        print(" effect = {}".format(self.get_variable('effect')))
        print(" colormode = {}\n".format(self.get_variable('colormode')))
    # ----------------------------------------------------------------------
    # method2: setDeviceStatus(postmsg), isPostmsgValid(postmsg), convertPostMsg(postmsg)
    def setDeviceStatus(self, postmsg):
        setDeviceStatusResult = True
        #Ex. postmsg = {"on":True,"bri":100,"hue":50260,"sat":200}
        _urlData = self.get_variable("address").replace(':80', '/api/newdeveloper/groups/0/')
        if self.isPostMsgValid(postmsg) == True: #check if the data is valid
            _data = json.dumps(self.convertPostMsg(postmsg))
            _data = _data.encode(encoding='utf_8')
            _request = urllib2.Request(_urlData+'action')
            _request.add_header('Content-Type','application/json')
            _request.get_method = lambda: 'PUT'
            try:
                _f = urllib2.urlopen(_request, _data) #when include data this become a POST command
                print(" {0}Agent for {1} is changing its status with {2} please wait ..."
                .format(self.variables.get('agent_id', None), self.variables.get('model', None), postmsg))
                print(" after send a POST request: {}".format(_f.read().decode('utf-8')))
            except:
                print("ERROR: classAPI_PhilipsHue connection failure! @ setDeviceStatus")
                setDeviceStatusResult = False
        else:
            print("The POST message is invalid, try again\n")
        return setDeviceStatusResult
            
    def isPostMsgValid(self,postmsg): #check validity of postmsg
        dataValidity = True
        #TODO algo to check whether postmsg is valid 
        return dataValidity
    
    def convertcolorxyYtoRGB(self,_xycolor,brightness):
        [_x,_y]=_xycolor
        _Y=brightness
        _xyY=xyYColor(_x,_y,_Y)
        _rgb=convert_color(_xyY, sRGBColor, target_illuminant='d50')
        maxrgb=max(_rgb.rgb_r,_rgb.rgb_g,_rgb.rgb_b)
        if maxrgb>1:
            _r=_rgb.rgb_r/maxrgb
            _g=_rgb.rgb_g/maxrgb
            _b=_rgb.rgb_b/maxrgb
        else:
            _r=_rgb.rgb_r
            _g=_rgb.rgb_g
            _b=_rgb.rgb_b
        _r=int(round(_r*255,0))
        _g=int(round(_g*255,0))
        _b=int(round(_b*255,0))       
        if _r<0:
            _r=_r+255
        if _g<0:
            _g=_g+255
        if _b<0:
            _b=_b+255 
        return (_r,_g,_b)
        
    def convertPostMsg(self,postmsg):
        msgToDevice = {}
        datacontainsRGB=False
        if 'color' in postmsg.keys():
            datacontainsRGB=True
            
        for k,v in postmsg.items():
            if k == 'status':
                if postmsg.get('status') == "ON":
                    msgToDevice['on'] = True
                elif postmsg.get('status') == "OFF":
                    msgToDevice['on'] = False
            elif k == 'brightness':
                msgToDevice['bri'] = int(round(float(postmsg.get('brightness'))*255.0/100.0,0))
            elif k == 'color':
                print(type(postmsg['color']))
                if type(postmsg['color']) == tuple:
                    _red, _green, _blue = postmsg['color']  # colors
                    rgb = sRGBColor(_red, _green, _blue, True)  # True for Digital 8-bit per channel
                    _xyY = convert_color(rgb, xyYColor, target_illuminant='d50')
                    msgToDevice['xy'] = [_xyY.xyy_x, _xyY.xyy_y]
                    msgToDevice['bri']= int(_xyY.xyy_Y*255)                  
                elif type(postmsg['color']) == list:
                    _red = postmsg['color'][0]
                    _green = postmsg['color'][1]
                    _blue = postmsg['color'][2]
                    rgb = sRGBColor(_red, _green, _blue, True)  # True for Digital 8-bit per channel
                    _xyY = convert_color(rgb, xyYColor, target_illuminant='d50')
                    msgToDevice['xy'] = [_xyY.xyy_x, _xyY.xyy_y]
                    msgToDevice['bri']= int(round(_xyY.xyy_Y*255,0))
            elif k == 'hue':
                if datacontainsRGB==False:
                    msgToDevice['hue'] = postmsg.get('hue')
                # msgToDevice['hue'] = 50000
            elif k == 'saturation':
                if datacontainsRGB==False:
                    msgToDevice['sat'] = int(round(float(postmsg.get('saturation'))*255.0/100.0,0))
            else:
                msgToDevice[k] = v
        return msgToDevice
    # ----------------------------------------------------------------------
    # method3: Identify this lights (Physically)
    def identifyDevice(self):
        identifyDeviceResult = False
        # _urlData = self.get_variable("address")
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
            print("ERROR: classAPI_PhilipsHue connection failure! @ identifyDevice")
        return identifyDeviceResult
    # ----------------------------------------------------------------------

# This main method will not be executed when this class is used as a module
def main():
    # Step1: create an object with initialized data from DeviceDiscovery Agent
    # requirements for instantiation1. model, 2.type, 3.api, 4. address
    PhilipsHue = API(model='Philips Hue',type='wifiLight',api='API3',address='http://38.68.232.134:80', agent_id='PhilipsHue1')
    print("{0}agent is initialzed for {1} using API={2} at {3}".format(PhilipsHue.get_variable('type'),PhilipsHue.get_variable('model'),PhilipsHue.get_variable('api'),PhilipsHue.get_variable('address')))
#   Step2: discovery all lights
#     PhilipsHue.getAllLights(PhilipsHue.get_variable('address'))
#   Step3: read current lights status
#     PhilipsHue.getLightStatus(PhilipsHue.get_variable('address'),1)
#   Step4: rename lights
#   PhilipsHue.setLightAttribute(PhilipsHue.get_variable('address'), 3,'name','office3')
#   Step5: set light states
#   PhilipsHue.setLightStatus(PhilipsHue.get_variable('address'),1,'sat',255)
#   PhilipsHue.setLightStatus(PhilipsHue.get_variable('address'),2,'sat',255)
#   PhilipsHue.setLightStatus(PhilipsHue.get_variable('address'),3,'sat',255)
#   PhilipsHue.setLightStatus(PhilipsHue.get_variable('address'),1,'effect','colorloop')
#   PhilipsHue.setLightStatus(PhilipsHue.get_variable('address'),2,'effect','colorloop')
#   PhilipsHue.setLightStatus(PhilipsHue.get_variable('address'),3,'effect','colorloop')
#   PhilipsHue.setLightStatus(PhilipsHue.get_variable('address'),1,'transitiontime',1)
#   PhilipsHue.setLightStatus(PhilipsHue.get_variable('address'),2,'transitiontime',10)
#   PhilipsHue.setLightStatus(PhilipsHue.get_variable('address'),3,'transitiontime',100)
#   Step6: light identification
#   PhilipsHue.identifyLight(PhilipsHue.get_variable('address'),1,10)
    PhilipsHue.getDeviceStatus()
#   PhilipsHue.setDeviceStatus({"status":"ON","brightness":100,"color":[95,227,18]})
#   time.sleep(10)
#   PhilipsHue.setDeviceStatus({"status":"ON","color":(55,13,255)})
    PhilipsHue.identifyDevice()
#   print test
#   PhilipsHue.setDeviceStatus({"status":"ON","saturation":100})
#   PhilipsHue.setDeviceStatus({"status":"ON","brightness":99,"hue":45678,"saturation":50})
    PhilipsHue.getDeviceStatus()
    print PhilipsHue.variables

if __name__ == "__main__": main()