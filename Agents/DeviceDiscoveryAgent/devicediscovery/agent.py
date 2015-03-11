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
__credits__ = []
__version__ = "1.2.1"
__maintainer__ = "Avijit Saha, Warodom Khamphanchai"
__email__ = "avijit@vt.edu, kwarodom@vt.edu"
__website__ = "kwarodom.wordpress.com"
__status__ = "Prototype"
__created__ = "2014-7-28 10:20:00"
__lastUpdated__ = "2015-02-11 16:35:27"
'''

import importlib
import psycopg2 #PostgresQL database adapter
import sys
import json
import datetime
import time
import logging
import os
import re
from volttron.lite.agent import BaseAgent, PublishMixin, periodic
from volttron.lite.agent import utils, matching
from volttron.lite.messaging import headers as headers_mod
from urlparse import urlparse
import settings
import random

utils.setup_logging()  # setup logger for debugging
_log = logging.getLogger(__name__)

#Step1: Agent Initialization
def DeviceDiscoveryAgent(config_path, **kwargs):
    config = utils.load_config(config_path)  # load the config_path from devicediscoveryagent.launch.json
    def get_config(name):
        try:
            value = kwargs.pop(name)  # from the **kwargs when call this function
        except KeyError:
            return config.get(name, '')

    #1. @params agent
    agent_id = get_config('agent_id')
    device_scan_time = get_config('device_scan_time')
    device_scan_time_multiplier = get_config('device_scan_time_multiplier')
    #device_scan_time_multiplier=1
    headers = {headers_mod.FROM: agent_id}
    publish_address = 'ipc:///tmp/volttron-lite-agent-publish'
    subscribe_address = 'ipc:///tmp/volttron-lite-agent-subscribe'
    topic_delim = '/'  # topic delimiter


    #3. @params agent & DB interfaces
    #@params DB interfaces
    db_database = settings.DATABASES['default']['NAME']
    db_host = settings.DATABASES['default']['HOST']
    db_port = settings.DATABASES['default']['PORT']
    db_user = settings.DATABASES['default']['USER']
    db_password = settings.DATABASES['default']['PASSWORD']
    db_table_device_info = settings.DATABASES['default']['TABLE_device_info']
    #db_table_dashboard_current_status = settings.DATABASES['default']['TABLE_dashboard_current_status']
    db_table_supported_devices = settings.DATABASES['default']['TABLE_supported_devices']

    #4. @params dummy devicediscovery agent setting
    dummy_device_discovery = settings.DUMMY_SETTINGS['dummy_discovery']
    num_of_dummy_hvac = settings.DUMMY_SETTINGS['number_of_hvac']
    num_of_dummy_lighting = settings.DUMMY_SETTINGS['number_of_lighting']
    num_of_dummy_plugload = settings.DUMMY_SETTINGS['number_of_plugload']

    #5. @params devicediscovery agent setting
    device_monitor_time = settings.DEVICES['device_monitor_time']
    findWiFi = settings.FIND_DEVICE_SETTINGS['findWiFi']
    findWiFiHue = settings.FIND_DEVICE_SETTINGS['findWiFiHue']
    findWiFiWeMo = settings.FIND_DEVICE_SETTINGS['findWiFiWeMo']

    #@paths
    PROJECT_DIR = settings.PROJECT_DIR
    Loaded_Agents_DIR = settings.Loaded_Agents_DIR
    Autostart_Agents_DIR = settings.Autostart_Agents_DIR
    Applications_Launch_DIR = settings.Applications_Launch_DIR
    Agents_Launch_DIR = settings.Agents_Launch_DIR

    class Agent(PublishMixin, BaseAgent):

        def __init__(self, **kwargs):
            super(Agent, self).__init__(**kwargs)
            # Connect to database
            self.con = psycopg2.connect(host=db_host, port=db_port, database=db_database,
                                        user=db_user, password=db_password)
            self.cur = self.con.cursor()  # open a cursor to perform database operations

            sys.path.append(PROJECT_DIR)

            self.device_scan_time = device_scan_time
            self.device_discovery_start_time = datetime.datetime.now()
            self.scan_for_devices = True

            self.findWiFi = findWiFi
            self.findWiFiHue = findWiFiHue
            self.findWiFiWeMo = findWiFiWeMo

            self.dummy_device_discovery = dummy_device_discovery
            if self.dummy_device_discovery:
                self.dummy_device_types={'hvac':{'thermostat':'thermostat'},'lighting':{'Philips':'lighting','WeMo_lighting':'lighting'},'plugload':{'WeMo_plugload':'plugload'}}
                self.num_of_dummy_devices=dict()
                self.num_of_dummy_devices['hvac'] = num_of_dummy_hvac
                self.num_of_dummy_devices['lighting'] = num_of_dummy_lighting
                self.num_of_dummy_devices['plugload'] = num_of_dummy_plugload

            self.new_discovery=True
            self.no_new_discovery_count=0

            try:
                # Find total number of devices in the dashboard_device_info table
                self.cur.execute("SELECT * FROM "+db_table_device_info)
                self.device_num = self.cur.rowcount  # count no. of devices discovered by Device Discovery Agent
                print "{} >> there are existing {} device(s) in database".format(agent_id, self.device_num)
                #if self.device_num != 0:  # change network status of devices to OFF (OFFLINE)
                #    rows = self.cur.fetchall()
                #    for row in rows:
                #        self.cur.execute("UPDATE "+db_table_device_info+" SET device_status=%s", ("OFF",))
                #        self.con.commit()
            except:
                self.device_num = 0

        def setup(self):
            super(Agent, self).setup()
            self.valid_data = False
            '''Discovery Processes'''
            while True:
                if self.scan_for_devices:
                    self.deviceScannerBehavior()
                    if not self.new_discovery:
                        self.no_new_discovery_count +=1
                    else:
                        self.no_new_discovery_count = 0
                    if self.no_new_discovery_count >= 10:
                        self.device_scan_time *= device_scan_time_multiplier
                    time.sleep(self.device_scan_time)
                else:
                    pass

        #deviceScannerBehavior (TickerBehavior)
        def deviceScannerBehavior(self):
            self.new_discovery=False
            print "Start Discovery Processes--------------------------------------------------"
            print "{} >> device next scan time in {} sec".format(agent_id, str(self.device_scan_time ))
            print "{} >> start_time {}".format(agent_id, str(self.device_discovery_start_time))
            self.device_discovery_time_now = datetime.datetime.now()
            print "{} >> current time {}".format(agent_id, str(self.device_discovery_time_now))
            print "{} >> is trying to discover all available devices\n".format(agent_id)

            # Check if dummy or real device discovery:
            if self.dummy_device_discovery:
                for device_type in self.dummy_device_types.keys():
                    if self.num_of_dummy_devices[device_type] > 0:
                        num_of_devices_to_discover_now = random.randint(1, self.num_of_dummy_devices[device_type])
                        type_no_of_device_to_discover_now = random.randint(0,len(self.dummy_device_types[device_type].keys())-1)
                        type_of_device_to_discover_now = self.dummy_device_types[device_type].keys()[type_no_of_device_to_discover_now]
                        device_number = num_of_devices_to_discover_now
                        while device_number > 0:
                            device_number -= self.findDevicesbytype("Dummy",self.dummy_device_types[device_type][type_of_device_to_discover_now],type_of_device_to_discover_now)
                        self.num_of_dummy_devices[device_type]-=num_of_devices_to_discover_now

            else:
                # Finding devices by type:

                if self.findWiFi: self.findDevicesbytype("WiFi","thermostat","thermostat")
                if self.findWiFiWeMo:
                    self.findDevicesbytype("WiFi","plugload","WeMo")
                    self.findDevicesbytype("WiFi","lighting","WeMo")
                if self.findWiFiHue: self.findDevicesbytype("WiFi","lighting","Philips")
            print "Stop Discovery Processes---------------------------------------------------"

        def findDevicesbytype(self,com_type,controller_type,discovery_type):
            #******************************************************************************************************

            self.cur.execute("SELECT device_type FROM "+db_table_device_info
                             +" WHERE device_type=%s", (controller_type,))
            num_Devices=self.cur.rowcount
            num_new_Devices = 0

            print "{} >> is finding available {} {} devices ...".format(agent_id,com_type,discovery_type)
            discovery_module = importlib.import_module("discoverAPI."+com_type)
            discovery_returns_ip=True

            discovered_address = discovery_module.discover(discovery_type)

            print discovered_address

            for address in discovered_address:
                if discovery_returns_ip:
                    ip_address = address
                    try:
                        macaddress = discovery_module.getMACaddress(discovery_type, ip_address)
                        if macaddress is not None:
                            _valid_macaddress = True
                        else:
                            _valid_macaddress = False
                    except:
                        _valid_macaddress = False

                else:
                    ip_address = None
                    macaddress = address
                    _valid_macaddress = True

                if _valid_macaddress:
                    if self.checkMACinDB(self.con, macaddress):
                        newdeviceflag = False
                        self.cur.execute("SELECT device_id from "+db_table_device_info
                                         +" where mac_address=%s",(macaddress,))
                        deviceID = self.cur.fetchone()[0]
                        agent_launch_file=deviceID+".launch.json"
                        self.cur.execute("SELECT bemoss from "+db_table_device_info
                                         +" where device_id=%s",(deviceID,))
                        bemoss_status = self.cur.fetchone()[0]
                        if self.device_agent_still_running(agent_launch_file):
                            print "{} >> {} for device with MAC address {} is still running"\
                                    .format(agent_id, agent_launch_file, macaddress)
                            if not bemoss_status:
                                print '{} >> Device with MAC address {} found to be Non-BEMOSS, Stopping agent {}'\
                                        .format(agent_id, macaddress, agent_launch_file)
                                os.system("bin/volttron-ctrl stop-agent " + agent_launch_file)
                            # else:
                            #     self.cur.execute("UPDATE "+db_table_device_info+" SET device_status=%s where "
                            #                                                               "id=%s", ("ON", deviceID))
                            #     self.con.commit()
                        else:
                            print "{} >> {} for device with MAC address {} is not running"\
                                    .format(agent_id, agent_launch_file, macaddress)
                            #restart agent if in BEMOSS Core
                            if bemoss_status:
                                self.cur.execute("SELECT device_type from "+db_table_device_info
                                                +" where device_id=%s",(deviceID,))
                                stopped_agent_device_type = self.cur.fetchone()[0]
                                self.cur.execute("SELECT zone_id from "+stopped_agent_device_type
                                                +" where "+stopped_agent_device_type+"_id=%s",(deviceID,))
                                stopped_agent_zone_id = self.cur.fetchone()[0]
                                if stopped_agent_zone_id == 999:
                                    self.launch_agent(Agents_Launch_DIR, agent_launch_file)
                                    print "{} >> {} has been restarted"\
                                            .format(agent_id, agent_launch_file)
                                else:
                                    print "{} >> {} is running on another node, ignoring restart"\
                                            .format(agent_id, agent_launch_file)
                                # self.cur.execute("UPDATE "+db_table_device_info+" SET device_status=%s where "
                                #                                                           "id=%s", ("ON", deviceID))
                                # self.con.commit()
                            else:
                                print '{} >> Device with MAC address {} found to be Non-BEMOSS'\
                                        .format(agent_id, macaddress)

                        #case2: new device has been discovered
                    else:
                        print '{} >> new device found with macaddress {}'\
                            .format(agent_id, macaddress)
                        newdeviceflag = True
                else:
                    print "Invalid MAC address at: {}"\
                        .format(address)
                    newdeviceflag = False

                if newdeviceflag:
                    model_info_received = False
                    try:
                        modelinfo = discovery_module.getmodelvendor(discovery_type, address)
                        if modelinfo != None:
                            deviceModel = modelinfo['model']
                            deviceVendor = modelinfo['vendor']
                            print 'Model information found: '
                            print {'model':deviceModel,'vendor':deviceVendor}
                            model_info_received = True
                    except:
                        pass

                    if model_info_received:
                        try:
                            self.cur.execute("SELECT device_type from "+db_table_supported_devices
                                             +" where vendor_name=%s and device_model=%s",(deviceVendor,deviceModel))
                            controller_type_from_model = self.cur.fetchone()[0]
                            supported=True
                        except:
                            supported=False
                        if (supported):
                            if (controller_type=='All') | (controller_type_from_model == controller_type):
                                self.device_num+=1
                                #deviceType = com_type + controller_type
                                deviceType = controller_type_from_model
                                self.cur.execute("SELECT device_model_id from "+db_table_supported_devices
                                                 +" where vendor_name=%s and device_model=%s",(deviceVendor,deviceModel))
                                device_type_id = self.cur.fetchone()[0]
                                self.cur.execute("SELECT identifiable from "+db_table_supported_devices
                                                 +" where vendor_name=%s and device_model=%s",(deviceVendor,deviceModel))
                                identifiable = self.cur.fetchone()[0]
                                if (ip_address != None):
                                    if ('/' in ip_address):
                                        IPparsed = urlparse(ip_address)
                                        print IPparsed
                                        deviceIP = str(IPparsed.netloc)
                                        if str(IPparsed.scheme) != '':
                                            address= str(IPparsed.scheme)+ "://" + str(IPparsed.netloc)
                                        else:
                                            address = deviceIP
                                        if ':' in deviceIP:
                                            deviceIP = deviceIP.split(':')[0]
                                    else:
                                        if ':' in ip_address:
                                            deviceIP = ip_address.split(':')[0]
                                        else:
                                            deviceIP = ip_address
                                        address = ip_address
                                else:
                                    deviceIP = ip_address
                                self.cur.execute("SELECT api_name from "+db_table_supported_devices
                                                 +" where vendor_name=%s and device_model=%s",(deviceVendor,deviceModel))
                                deviceAPI = self.cur.fetchone()[0]
                                deviceID = device_type_id+macaddress
                                # self.cur.execute("INSERT INTO "+db_table_device_info+" VALUES(%s,%s,%s,%s,%s,%s,%s,999,%s,'ON')",
                                #                  (deviceID, deviceID, deviceType+str(self.device_num), deviceType, device_type_id,
                                #                   deviceVendor, deviceModel, macaddress))
                                self.cur.execute("INSERT INTO "+db_table_device_info+" VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                                                 (deviceID, deviceType, deviceVendor, deviceModel, device_type_id, macaddress,
                                                  None, None, identifiable, com_type, str(datetime.datetime.now()), macaddress, True))
                                self.con.commit()
                                self.cur.execute("INSERT INTO "+deviceType+" ("+deviceType+"_id, ip_address,nickname,zone_id,network_status) VALUES(%s,%s,%s,%s,%s)",
                                                 (deviceID, deviceIP,deviceType+str(self.device_num),999,'ONLINE'))
                                self.con.commit()
                                agent_name = deviceType.replace('_','')
                                num_new_Devices+=1
                                #After found new device-> Assign a suitable agent to each device to communicate, control, and collect data
                                print('Now DeviceDiscoverAgent is assigning a suitable agent to the discovered Weme device to communicate, control, and collect data')
                                self.write_launch_file(agent_name+"agent", deviceID, device_monitor_time, deviceModel,
                                               deviceVendor, deviceType, deviceAPI, address, db_host, db_port,
                                               db_database, db_user, db_password)
                                self.launch_agent(Agents_Launch_DIR, deviceID+".launch.json")
                                self.new_discovery=True
                            else:
                                pass
                        else:
                            print "Device currently not supported by BEMOSS"

                    else:
                        print 'Unable to get device model information. Ignoring device...'

            #Print how many WiFi devices this DeviceDiscoverAgent found!
            print("{} >> Found {} new {} {} devices".format(agent_id,num_new_Devices,com_type,controller_type))
            print("{} >> There are existing {} {} {} devices\n".format(agent_id,num_Devices,com_type,controller_type))
            print " "
            return num_new_Devices

        def launch_agent(self, dir, launch_file):
            _launch_file = os.path.join(dir, launch_file)
            os.system("bin/volttron-ctrl stop-agent " + launch_file)
            os.system("bin/volttron-ctrl load-agent " + _launch_file)
            os.system("bin/volttron-ctrl start-agent " + os.path.basename(_launch_file))
            os.system("bin/volttron-ctrl list-agent")
            print "{} >> has successfully launched {} located in {}".format(agent_id, launch_file, dir)

        def checkMACinDB(self, conn, macaddr):
            cur = conn.cursor()
            cur.execute("SELECT device_id FROM "+db_table_device_info+" WHERE mac_address=%(id)s",
                        {'id': macaddr})
            if cur.rowcount != 0:
                mac_already_in_db = True
            else:
                mac_already_in_db = False
            return mac_already_in_db

        def device_agent_still_running(self,agent_launch_filename):
            os.system("bin/volttron-ctrl list-agent > running_agents.txt")
            infile = open('running_agents.txt', 'r')
            agent_still_running = False
            reg_search_term = agent_launch_filename
            for line in infile:
                #print(line, end='') #write to a next file name outfile
                match = re.search(reg_search_term, line) and re.search('running', line)
                if match:  # The agent for this device is running
                    agent_still_running = True
                else:
                    pass
            infile.close()
            return agent_still_running

        def write_launch_file(self, executable, deviceID, device_monitor_time, deviceModel, deviceVendor, deviceType,
                              api, address, db_host, db_port, db_database, db_user, db_password):
            data= {
                    "agent": {
                        "exec": executable+"-0.1-py2.7.egg --config \"%c\" --sub \"%s\" --pub \"%p\""
                    },
                    "agent_id": deviceID,
                    "device_monitor_time": device_monitor_time,
                    "model": deviceModel,
                    "vendor":deviceVendor,
                    "type": deviceType,
                    "api": api,
                    "address": address,
                    "db_host": db_host,
                    "db_port": db_port,
                    "db_database": db_database,
                    "db_user": db_user,
                    "db_password": db_password,
                    "building_name": "bemoss",
                    "zone_id" : 999
                }
            __launch_file = os.path.join(Agents_Launch_DIR+deviceID+".launch.json")
            with open(__launch_file, 'w') as outfile:
                json.dump(data, outfile, indent=4, sort_keys=True)

    Agent.__name__ = 'DeviceDiscoveryAgent'
    return Agent(**kwargs)

def main(argv=sys.argv):
    '''Main method called by the eggsecutable.'''
    utils.default_main(DeviceDiscoveryAgent, description='Device Discovery agent', argv=argv)

if __name__ == '__main__':
    # Entry point for script
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        pass
