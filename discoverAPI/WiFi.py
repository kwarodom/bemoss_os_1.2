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

__author__ = "Avijit Saha"
__credits__ = ""
__version__ = "1.2.1"
__maintainer__ = "Avijit Saha"
__email__ = "avijit@vt.edu"
__website__ = ""
__status__ = "Prototype"
__created__ = "2014-8-29 17:15:00"
__lastUpdated__ = "2015-02-11 21:50:37"
'''

import socket
import httplib
import StringIO
import re
import json
import urllib2
from xml.dom import minidom
import requests
 
class SSDPResponse(object):
    class _FakeSocket(StringIO.StringIO):
        def makefile(self, *args, **kw):
            return self
    def __init__(self, response):
        r = httplib.HTTPResponse(self._FakeSocket(response))
        r.begin()
        self.location = r.getheader("location")
        #self.usn = r.getheader("usn")
        #self.st = r.getheader("st")
        #self.cache = r.getheader("cache-control").split("=")[1]
    def __repr__(self):
        #return "<SSDPResponse({location}, {st}, {usn})>".format(**self.__dict__)
        return self.location
    
class SSDPResponseLocation(object):
    def __init__(self, response):
        tokens=response.split('\r\n')
        self.location = 'dummy'
        for token in tokens:
            if re.search('LOCATION: ',token):
                self.location=token.replace('LOCATION: ','')
                break
    def __repr__(self):
        return self.location
    
def parseJSONresponse(data,key):
    theJSON = json.loads(data)
    return theJSON[key]

class Nest:
    def __init__(self, username, password, serial=None, index=0, units="F", debug=False):
        self.username = username
        self.password = password
        self.serial = serial
        self.units = units
        self.index = index
        self.debug = debug

    def login(self):

       try:
           response = requests.post("https://home.nest.com/user/login",
                                    data = {"username":self.username, "password" : self.password},
                                    headers = {"user-agent":"Nest/1.1.0.10 CFNetwork/548.0.4"})

           response.raise_for_status()

           res = response.json()
           self.transport_url = res["urls"]["transport_url"]
           self.access_token = res["access_token"]
           self.userid = res["userid"]
       except:
           print "Nest login failed, try again"
       # print self.transport_url, self.access_token, self.userid

    def get_status(self):
       try:
           response = requests.get(self.transport_url + "/v2/mobile/user." + self.userid,
                                   headers={"user-agent":"Nest/1.1.0.10 CFNetwork/548.0.4",
                                            "Authorization":"Basic " + self.access_token,
                                            "X-nl-user-id": self.userid,
                                            "X-nl-protocol-version": "1"})

           response.raise_for_status()
           res = response.json()

           self.structure_id = res["structure"].keys()[0]

           if (self.serial is None):
              self.device_id = res["structure"][self.structure_id]["devices"][self.index]
              self.serial = self.device_id.split(".")[1]

              self.status = res
       except:
           print "Nest get status failed, try again"

def discover(type, timeout=2, retries=1):

    if (type == 'Nest'):
        responses = list()
        try:
            Nestobject = Nest('kwarodom@vt.edu','DRTeam@900')
            Nestobject.login()
            Nestobject.get_status()
            responses.append(str(Nestobject.status["device"][Nestobject.serial]["local_ip"]))
        except:
            print "Nest discovery failed, try again"
        return responses

    else:
        group = ("239.255.255.250", 1900)
        if type=='thermostat':
            message="TYPE: WM-DISCOVER\r\nVERSION: 1.0\r\n\r\nservices: com.marvell.wm.system*\r\n\r\n"
        else:
            message = "\r\n".join([
                'M-SEARCH * HTTP/1.1',
                'HOST: {0}:{1}',
                'MAN: "ssdp:discover"',
                'ST: {st}','MX: 3','',''])
            if type=='WeMo':
                service="upnp:rootdevice"
            elif type=='Philips':
                service="urn:schemas-upnp-org:device:Basic:1"

            message=message.format(*group, st=service)

        socket.setdefaulttimeout(timeout)
        responses = {}
        for _ in range(retries):
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
            try:
                sock.sendto(message, group)
            except:
                print("[Errno 101] Network is unreachable")

            responses=list()
            while True:
                try:
                    response = str(SSDPResponseLocation(sock.recv(1024)))
                    if type=="thermostat":
                        if "/sys" in response and response not in responses:
                            responses.append(response)
                    elif type=="WeMo":
                        if (':49153/setup.xml' in response or ':49154/setup.xml' in response) and response not in responses:
                            responses.append(response)
                    elif type=="Philips":
                        if ":80/description.xml" in response and response not in responses:
                            responses.append(response)
                except socket.timeout:
                    break

        return responses

def getMACaddress(type,ipaddress):
    if type == "thermostat":
        try:
            deviceuuidUrl = urllib2.urlopen(ipaddress, timeout=5)
            deviceuuid=parseJSONresponse(deviceuuidUrl.read().decode("utf-8"),"uuid")
            deviceuuidUrl.close()
            return deviceuuid
        except socket.timeout, e:
            print "There was an error getting MAC address due to: %r" % e
    elif type=="Philips":
        deviceUrl = urllib2.urlopen(ipaddress)
        dom=minidom.parse(deviceUrl)
        serialid=dom.getElementsByTagName('serialNumber')[0].firstChild.data
        deviceUrl.close()
        return serialid
    elif type=="WeMo":
        deviceUrl = urllib2.urlopen(ipaddress)
        dom=minidom.parse(deviceUrl)
        macid=dom.getElementsByTagName('macAddress')[0].firstChild.data
        deviceUrl.close()
        return macid
    elif type=="Nest":
        Nestobject = Nest('kwarodom@vt.edu','DRTeam@900')
        Nestobject.login()
        Nestobject.get_status()
        macid = str(Nestobject.status["device"][Nestobject.serial]["mac_address"])
        return macid
    
def getmodelvendor(type,ipaddress):
    if type=="thermostat":
        modeladdress=ipaddress.replace('/sys','/tstat/model')
        deviceModelUrl = urllib2.urlopen(modeladdress)           
        if (deviceModelUrl.getcode()==200):
            deviceModel = parseJSONresponse(deviceModelUrl.read().decode("utf-8"),"model")
        deviceVendor = "RadioThermostat"
        deviceModelUrl.close()
        return {'model':deviceModel,'vendor':deviceVendor}
    elif type=="Philips":
        deviceUrl = urllib2.urlopen(ipaddress)
        dom=minidom.parse(deviceUrl)
        deviceModel=dom.getElementsByTagName('modelName')[0].firstChild.data
        deviceVendor=dom.getElementsByTagName('manufacturer')[0].firstChild.data
        deviceUrl.close()
        return {'model':deviceModel,'vendor':deviceVendor}
    elif type=="WeMo":
        deviceUrl = urllib2.urlopen(ipaddress)
        dom=minidom.parse(deviceUrl)
        deviceModel=dom.getElementsByTagName('modelName')[0].firstChild.data
        deviceVendor=dom.getElementsByTagName('manufacturer')[0].firstChild.data
        deviceUrl.close()
        return {'model':deviceModel,'vendor':deviceVendor}
    elif type=="Nest":
        return {'model':"Nest",'vendor':"Nest"}