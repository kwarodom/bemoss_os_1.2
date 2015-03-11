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
__created__ = "2014-10-13 18:45:40"
__lastUpdated__ = "2015-02-11 16:59:47"
'''

import sys
import json
import importlib
import logging
from volttron.lite.agent import BaseAgent, PublishMixin, periodic
from volttron.lite.agent import utils, matching
from volttron.lite.messaging import headers as headers_mod
import datetime
from bemoss.communication.Email import EmailService
import psycopg2  # PostgresQL database adapter
import psycopg2.extras
import settings
import time
import socket

utils.setup_logging()
_log = logging.getLogger(__name__)

# Step1: Agent Initialization
def ThermostatAgent(config_path, **kwargs):
    config = utils.load_config(config_path)

    def get_config(name):
        try:
            kwargs.pop(name)
        except KeyError:
            return config.get(name, '')

    # 1. @params agent
    agent_id = get_config('agent_id')
    LOG_DATA_PERIOD = get_config('poll_time')
    device_monitor_time = get_config('device_monitor_time')
    publish_address = 'ipc:///tmp/volttron-lite-agent-publish'
    subscribe_address = 'ipc:///tmp/volttron-lite-agent-subscribe'
    debug_agent = False
    agentknowledge = dict(day=["day"], hour=["hour"], minute=["minute"], temperature=["temp", "temperature",
                      "current_temp"], thermostat_mode=["tmode", "ther_mode", "thermostat_mode"],
                      fan_mode=["fmode", "fan_mode"], heat_setpoint=["t_heat", "temp_heat", "heat_setpoint"],
                      cool_setpoint=["t_cool", "temp_cool", "cool_setpoint"], thermostat_state=["tstate",
                      "thermostat_state"], fan_state=["fstate", "fan_state"])
    agentAPImapping = dict(temperature=[], thermostat_mode=[], fan_mode=[], heat_setpoint=[],
                           cool_setpoint=[], thermostat_state=[], fan_state=[])

    # 2. @params device_info
    building_name = get_config('building_name')
    zone_id = get_config('zone_id')
    # room = get_config('room')
    model = get_config('model')
    device_type = get_config('type')
    address = get_config('address')
    _address = address
    _address = _address.replace('http://', '')
    _address = _address.replace('https://', '')
    try:  # validate whether or not address is an ip address
        socket.inet_aton(_address)
        ip_address = _address
        # print "yes ip_address is {}".format(ip_address)
    except socket.error:
        # print "yes ip_address is None"
        ip_address = None
    identifiable = get_config('identifiable')
    # mac_address = get_config('mac_address')

    # 3. @params agent & DB interfaces
    # get database parameters from settings.py, add db_table for specific table
    db_host = get_config('db_host')
    db_port = get_config('db_port')
    db_database = get_config('db_database')
    db_user = get_config('db_user')
    db_password = get_config('db_password')
    db_table_thermostat = settings.DATABASES['default']['TABLE_thermostat']
    db_table_notification_event = settings.DATABASES['default']['TABLE_notification_event']

    # construct _topic_Agent_UI based on data obtained from DB
    _topic_Agent_UI = building_name+'/'+str(zone_id)+'/'+device_type+'/'+agent_id + '/'
    # print(_topic_Agent_UI)

    # construct _topic_Agent_sMAP based on data obtained from DB
    _topic_Agent_sMAP = 'datalogger/log/'+building_name+'/'+str(zone_id)+'/'+device_type+'/'+agent_id
    # print(_topic_Agent_sMAP)

    # 4. @params device_api
    api = get_config('api')
    # discovery agent locate the location of api in launch file e.g. "api": "testAPI.classAPI_RadioThermostat",
    apiLib = importlib.import_module("testAPI."+api)
    # print("testAPI."+api)

    # 4.1 initialize thermostat device object
    Thermostat = apiLib.API(model=model, device_type=device_type, api=api, address=address, agent_id=agent_id)

    print("{0}agent is initialized for {1} using API={2} at {3}".format(agent_id, Thermostat.get_variable('model'),
                                                                        Thermostat.get_variable('api'),
                                                                        Thermostat.get_variable('address')))

    # 5. @params notification_info
    send_notification = True
    email_fromaddr = settings.NOTIFICATION['email']['fromaddr']
    email_recipients = settings.NOTIFICATION['email']['recipients']
    email_username = settings.NOTIFICATION['email']['username']
    email_password = settings.NOTIFICATION['email']['password']
    email_mailServer = settings.NOTIFICATION['email']['mailServer']
    notify_heartbeat = settings.NOTIFICATION['heartbeat']

    class Agent(PublishMixin, BaseAgent):

        # 1. agent initialization
        def __init__(self, **kwargs):
            super(Agent, self).__init__(**kwargs)
            #1. initialize all agent variables
            self.variables = kwargs
            self.valid_data = False
            self._keep_alive = True
            self.first_time_update = True
            self.topic = _topic_Agent_sMAP
            self.ip_address = ip_address if ip_address != None else None
            self.flag = 1
            self.authorized_thermostat_mode = None
            self.authorized_fan_mode = None
            self.authorized_heat_setpoint = None
            self.authorized_cool_setpoint = None
            self.time_sent_notifications_device_tampering = datetime.datetime.now()
            self.first_time_detect_device_tampering = True
            self.event_ids = list()
            self.time_sent_notifications = {}
            self.notify_heartbeat = notify_heartbeat
            self._override = False
            #2. setup connection with db -> Connect to bemossdb database
            try:
                self.con = psycopg2.connect(host=db_host, port=db_port, database=db_database, user=db_user,
                                            password=db_password)
                self.cur = self.con.cursor()  # open a cursor to perform database operations
                print("{} connects to the database name {} successfully".format(agent_id, db_database))
            except:
                print("ERROR: {} fails to connect to the database name {}".format(agent_id, db_database))
            #3. send notification to notify building admin
            self.send_notification = send_notification
            # self.time_send_notification = 0
            # if self.send_notification:
            self.subject = 'Message from ' + agent_id
            #     self.text = 'Now an agent device_type {} for {} with API {} at address {} is launched!'.format(
            #         Thermostat.get_variable('device_type'), Thermostat.get_variable('model'),
            #         Thermostat.get_variable('api'), Thermostat.get_variable('address'))
            #     emailService = EmailService()
            #     emailService.sendEmail(email_fromaddr, email_recipients, email_username, email_password, self.subject,
            #                            self.text, email_mailServer)

        # These set and get methods allow scalability
        def set_variable(self, k, v):  # k=key, v=value
            self.variables[k] = v
    
        def get_variable(self, k):
            return self.variables.get(k, None)  # default of get_variable is none
        
        # 2. agent setup method
        def setup(self):
            super(Agent, self).setup()
            #1. Do a one time push when we start up so we don't have to wait for the periodic
            self.timer(1, self.deviceMonitorBehavior)
            if identifiable == "True": Thermostat.identifyDevice()
            try:
                # update initial value of override column of a thermostat to False
                self.cur.execute("UPDATE "+db_table_thermostat+" SET override=%s WHERE thermostat_id=%s",
                                 (self._override, agent_id))
                self.con.commit()
            except:
                print "{} >> cannot update override column of thermostat".format(agent_id)

        # 3. deviceMonitorBehavior (CyclicBehavior)
        @periodic(device_monitor_time)
        def deviceMonitorBehavior(self):
            # step1: get current status of a thermostat, then map keywords and variables to agent knowledge
            try:
                Thermostat.getDeviceStatus()
                # mapping variables from API to Agent's knowledge
                for APIKeyword, APIvariable in Thermostat.variables.items():
                    if debug_agent: print (APIKeyword, APIvariable)
                    self.set_variable(self.getKeyword(APIKeyword), APIvariable)  # set variables of agent from API variables
                    agentAPImapping[self.getKeyword(APIKeyword)] = APIKeyword  # map keyword of agent and API
            except:
                print("device connection is not successful")

            if self.first_time_update:
                if self.get_variable('heat_setpoint') is None: self.set_variable('heat_setpoint', 70)
                else: pass
                if self.get_variable('cool_setpoint') is None: self.set_variable('cool_setpoint', 70)
                else: pass
                self.first_time_update = False
            else:
                pass

            # step2: send notification to a user if required
            if self.send_notification:
                self.track_event_send_notification()

            # step3: update PostgresQL (meta-data) database
            try:
                self.cur.execute("UPDATE "+db_table_thermostat+" SET temperature=%s WHERE thermostat_id=%s",
                                 (self.get_variable('temperature'), agent_id))
                self.con.commit()
                self.cur.execute("UPDATE "+db_table_thermostat+" SET fan_mode=%s WHERE thermostat_id=%s",
                                 (self.get_variable('fan_mode'), agent_id))
                self.con.commit()
                if self.get_variable('battery') is not None:
                    self.cur.execute("UPDATE "+db_table_thermostat+" SET battery=%s WHERE thermostat_id=%s",
                                 (self.get_variable('battery'), agent_id))
                    self.con.commit()
                if self.get_variable('thermostat_mode') == "HEAT":
                    self.cur.execute("UPDATE "+db_table_thermostat+" SET heat_setpoint=%s WHERE thermostat_id=%s",
                                     (self.get_variable('heat_setpoint'), agent_id))
                    self.con.commit()
                    self.cur.execute("UPDATE "+db_table_thermostat+" SET thermostat_mode=%s WHERE thermostat_id=%s",
                                     ('HEAT', agent_id))
                    self.con.commit()
                elif self.get_variable('thermostat_mode') == "COOL":
                    self.cur.execute("UPDATE "+db_table_thermostat+" SET cool_setpoint=%s WHERE thermostat_id=%s",
                                     (self.get_variable('cool_setpoint'), agent_id))
                    self.con.commit()
                    self.cur.execute("UPDATE "+db_table_thermostat+" SET thermostat_mode=%s WHERE thermostat_id=%s",
                                     ('COOL', agent_id))
                    self.con.commit()
                elif self.get_variable('thermostat_mode') == "OFF":
                    self.cur.execute("UPDATE "+db_table_thermostat+" SET thermostat_mode=%s WHERE thermostat_id=%s",
                                     ('OFF', agent_id))
                    self.con.commit()
                elif self.get_variable('thermostat_mode') == "AUTO":
                    self.cur.execute("UPDATE "+db_table_thermostat+" SET thermostat_mode=%s WHERE thermostat_id=%s",
                                     ('AUTO', agent_id))
                    self.con.commit()
                else:
                    pass

                if self.ip_address != None:
                    psycopg2.extras.register_inet()
                    _ip_address = psycopg2.extras.Inet(self.ip_address)
                    self.cur.execute("UPDATE "+db_table_thermostat+" SET ip_address=%s WHERE thermostat_id=%s",
                                     (_ip_address, agent_id))
                    self.con.commit()
                _time_stamp_last_scanned = str(datetime.datetime.now())
                self.cur.execute("UPDATE "+db_table_thermostat+" SET last_scanned_time=%s "
                                 "WHERE thermostat_id=%s",
                                 (_time_stamp_last_scanned, agent_id))
                self.con.commit()
                print("{} updates database name {} during deviceMonitorBehavior successfully".format(agent_id,db_database))
            except:
                print("ERROR: {} failed to update database name {}".format(agent_id, db_database))

            # step4: update sMAP (time-series) database
            try:
                self.publish_logdata1()
                self.publish_logdata2()
                self.publish_logdata3()
                self.publish_logdata4()
                self.publish_logdata5()
                self.publish_logdata6()
                self.publish_logdata7()
                print "{} success update sMAP database\n".format(agent_id)
            except:
                print("ERROR: {} fails to update sMAP database".format(agent_id))

            # step5: debug agent knowledge
            if debug_agent:
                print("printing agent's knowledge")
                for k, v in self.variables.items():
                    print (k, v)
                print('')

            if debug_agent:
                print("printing agentAPImapping's fields")
                for k, v in agentAPImapping.items():
                    if k is None:
                        agentAPImapping.update({v: v})
                        agentAPImapping.pop(k)
                for k, v in agentAPImapping.items():
                    print (k, v)
            
        def getKeyword(self, APIKeyword):
            for k, v in agentknowledge.items():
                if APIKeyword in agentknowledge[k]:
                    return k
                    flag = 1
                    break
                else:
                    flag = 0
                    pass
            if flag == 0:  # if flag still 0 means that a APIKeyword is not in an agent knowledge,
                           # then add it to agent knowledge
                return APIKeyword
        
        # 4. updateUIBehavior (generic behavior)
        @matching.match_exact('/ui/agent/'+_topic_Agent_UI+'device_status')
        def updateUIBehavior(self, topic, headers, message, match):
            print agent_id + " got\nTopic: {topic}".format(topic=topic)
            print "Headers: {headers}".format(headers=headers)
            print "Message: {message}\n".format(message=message)
            #reply message
            topic = '/agent/ui/'+_topic_Agent_UI+'device_status/response'
            # now = datetime.utcnow().isoformat(' ') + 'Z'
            headers = {
                'AgentID': agent_id,
                headers_mod.CONTENT_TYPE: headers_mod.CONTENT_TYPE.JSON,
                # headers_mod.DATE: now,
                headers_mod.FROM: agent_id,
                headers_mod.TO: 'ui'
            }
            #TODO add battery field to _data
            if self.get_variable('battery') != None:
                _data = {'temperature': self.get_variable('temperature'), 'thermostat_mode':
                         self.get_variable('thermostat_mode'), 'fan_mode': self.get_variable('fan_mode'),
                         'heat_setpoint': self.get_variable('heat_setpoint'), 'cool_setpoint': self.get_variable('cool_setpoint'),
                         'thermostat_state': self.get_variable('thermostat_state'), 'fan_state': self.get_variable('fan_state'),
                         'battery': self.get_variable('battery'), 'override': self._override
                }
            else:
                _data = {'temperature': self.get_variable('temperature'), 'thermostat_mode':
                         self.get_variable('thermostat_mode'), 'fan_mode': self.get_variable('fan_mode'),
                         'heat_setpoint': self.get_variable('heat_setpoint'), 'cool_setpoint': self.get_variable('cool_setpoint'),
                         'thermostat_state': self.get_variable('thermostat_state'), 'fan_state': self.get_variable('fan_state'),
                         'override': self._override
                }
            message = json.dumps(_data) 
            message = message.encode(encoding='utf_8')
            self.publish(topic, headers, message)

        # 5. deviceControlBehavior (generic behavior)
        @matching.match_exact('/ui/agent/'+_topic_Agent_UI+'update')
        def deviceControlBehavior(self, topic, headers, message, match):
            print agent_id + " got\nTopic: {topic}".format(topic=topic)
            print "Headers: {headers}".format(headers=headers)
            print "Message: {message}\n".format(message=message)
            #step1: change device status according to the receive message
            if self.isPostmsgValid(message[0]):  # check if the data is valid
                # _data = json.dumps(message[0])
                _data = json.loads(message[0])
                for k, v in _data.items():
                    if k == 'thermostat_mode':
                        self.authorized_thermostat_mode = _data.get('thermostat_mode')
                        if _data.get('thermostat_mode') == "HEAT":
                            for k, v in _data.items():
                                if k == 'heat_setpoint': self.authorized_heat_setpoint = _data.get('heat_setpoint')
                                else: pass
                        elif _data.get('thermostat_mode') == "COOL":
                            for k, v in _data.items():
                                if k == 'cool_setpoint': self.authorized_cool_setpoint = _data.get('cool_setpoint')
                                else: pass
                    elif k == 'fan_mode':
                        self.authorized_fan_mode = _data.get('fan_mode')
                    else: pass
                print "{} >> self.authorized_thermostat_mode {}".format(agent_id, self.authorized_thermostat_mode)
                print "{} >> self.authorized_heat_setpoint {}".format(agent_id, self.authorized_heat_setpoint)
                print "{} >> self.authorized_cool_setpoint {}".format(agent_id, self.authorized_cool_setpoint)
                print "{} >> self.authorized_fan_mode {}".format(agent_id, self.authorized_fan_mode)
                setDeviceStatusResult = Thermostat.setDeviceStatus(json.loads(message[0]))  # convert received message from string to JSON
                #TODO need to do additional checking whether the device setting is actually success!!!!!!!!
                #step2: update agent's knowledge on this device
                Thermostat.getDeviceStatus()
                #step3: send reply message back to the UI
                topic = '/agent/ui/'+_topic_Agent_UI+'update/response'
                # now = datetime.utcnow().isoformat(' ') + 'Z'
                headers = {
                    'AgentID': agent_id,
                    headers_mod.CONTENT_TYPE: headers_mod.CONTENT_TYPE.PLAIN_TEXT,
                    # headers_mod.DATE: now,
                }
                if setDeviceStatusResult:
                    message = 'success'
                else:
                    message = 'failure'
            else:
                print("The POST message is invalid, check thermostat_mode, heat_setpoint, cool_setpoint "
                      "setting and try again\n")
                message = 'failure'
            self.publish(topic, headers, message)

        def isPostmsgValid(self, postmsg):  # check validity of postmsg
            dataValidity = True
            try:
                # _data = json.dumps(postmsg)
                _data = json.loads(postmsg)
                for k, v in _data.items():
                    if k == 'thermostat_mode':
                        self.authorized_thermostat_mode = _data.get('thermostat_mode')
                        if _data.get('thermostat_mode') == "HEAT":
                            for k, v in _data.items():
                                if k == 'heat_setpoint': self.authorized_heat_setpoint = _data.get('heat_setpoint')
                                elif k == 'cool_setpoint':
                                    dataValidity = False
                                    break
                                else: pass
                        elif _data.get('thermostat_mode') == "COOL":
                            for k, v in _data.items():
                                if k == 'cool_setpoint': self.authorized_cool_setpoint = _data.get('cool_setpoint')
                                elif k == 'heat_setpoint':
                                    dataValidity = False
                                    break
                                else: pass
                    elif k == 'fan_mode':
                        self.authorized_fan_mode = _data.get('fan_mode')
                    else: pass
            except:
                dataValidity = True
                print("dataValidity failed to validate data comes from UI")
            return dataValidity

        # 6. deviceIdentifyBehavior (generic behavior)
        @matching.match_exact('/ui/agent/'+_topic_Agent_UI+'identify')
        def deviceIdentifyBehavior(self, topic, headers, message, match):
            print agent_id+ " got\nTopic: {topic}".format(topic=topic)
            print "Headers: {headers}".format(headers=headers)
            print "Message: {message}\n".format(message=message)
            #step1: change device status according to the receive message
            identifyDeviceResult = Thermostat.identifyDevice()
            #TODO need to do additional checking whether the device setting is actually success!!!!!!!!
            #step2: send reply message back to the UI
            topic = '/agent/ui/'+_topic_Agent_UI+'identify/response'
            # now = datetime.utcnow().isoformat(' ') + 'Z'
            headers = {
                'AgentID': agent_id,
                headers_mod.CONTENT_TYPE: headers_mod.CONTENT_TYPE.PLAIN_TEXT,
                # headers_mod.DATE: now,
            }
            if identifyDeviceResult:
                message = 'success'
            else:
                message = 'failure'
            self.publish(topic, headers, message)
            
        # Filter agent knowledge before sending out data to sMAP
        def publish_logdata1(self):
            headers = {
                headers_mod.FROM: agent_id,
                headers_mod.CONTENT_TYPE: headers_mod.CONTENT_TYPE.JSON,
            }
            mytime = int(time.time())
            content = {
                "temperature": {
                    "Readings": [[mytime, float(self.get_variable("temperature"))]],
                    "Units": "F",
                    "data_type": "double"
                }
            }
            print("{} published temperature to an IEB".format(agent_id))
            self.publish(_topic_Agent_sMAP, headers, json.dumps(content))

        def publish_logdata2(self):
            headers = {
                headers_mod.FROM: agent_id,
                headers_mod.CONTENT_TYPE: headers_mod.CONTENT_TYPE.JSON,
            }
            mytime = int(time.time())
            if self.get_variable("thermostat_mode") == "OFF":
                _thermostat_mode = 0
            elif self.get_variable("thermostat_mode") == "HEAT":
                _thermostat_mode = 1
            elif self.get_variable("thermostat_mode") == "COOL":
                _thermostat_mode = 2
            elif self.get_variable("thermostat_mode") == "AUTO":
                _thermostat_mode = 3
            else:
                _thermostat_mode = 4
            content = {
                "thermostat_mode": {
                    "Readings": [[mytime, float(_thermostat_mode)]],
                    "Units": "N/A",
                    "data_type": "double"
                }
            }
            print("{} published thermostat_mode to an IEB".format(agent_id))
            self.publish(_topic_Agent_sMAP, headers, json.dumps(content))

        def publish_logdata3(self):
            headers = {
                headers_mod.FROM: agent_id,
                headers_mod.CONTENT_TYPE: headers_mod.CONTENT_TYPE.JSON,
            }
            mytime = int(time.time())
            if self.get_variable("fan_mode") == "AUTO":
                _fan_mode = 0
            elif self.get_variable("fan_mode") == "CIRCULATE":
                _fan_mode = 1
            elif self.get_variable("fan_mode") == "ON":
                _fan_mode = 2
            else:
                _fan_mode = 3
            content = {
                "fan_mode": {
                    "Readings": [[mytime, float(_fan_mode)]],
                    "Units": "N/A",
                    "data_type": "double"
                }
            }
            print("{} published fan_mode to an IEB".format(agent_id))
            self.publish(_topic_Agent_sMAP, headers, json.dumps(content))

        def publish_logdata4(self):
            headers = {
                headers_mod.FROM: agent_id,
                headers_mod.CONTENT_TYPE: headers_mod.CONTENT_TYPE.JSON,
            }
            mytime = int(time.time())
            content = {
                "heat_setpoint": {
                    "Readings": [[mytime, float(self.get_variable("heat_setpoint"))]],
                    "Units": "F",
                    "data_type": "double"
                }
            }
            print("{} published heat_setpoint to an IEB".format(agent_id))
            self.publish(_topic_Agent_sMAP, headers, json.dumps(content))

        def publish_logdata5(self):
            headers = {
                headers_mod.FROM: agent_id,
                headers_mod.CONTENT_TYPE: headers_mod.CONTENT_TYPE.JSON,
            }
            mytime = int(time.time())
            content = {
                "cool_setpoint": {
                    "Readings": [[mytime, float(self.get_variable("cool_setpoint"))]],
                    "Units": "F",
                    "data_type": "double"
                }
            }
            print("{} published cool_setpoint to an IEB".format(agent_id))
            self.publish(_topic_Agent_sMAP, headers, json.dumps(content))

        def publish_logdata6(self):
            headers = {
                headers_mod.FROM: agent_id,
                headers_mod.CONTENT_TYPE: headers_mod.CONTENT_TYPE.JSON,
            }
            mytime = int(time.time())
            if self.get_variable("thermostat_state") == "OFF":
                _thermostat_state = 0
            elif self.get_variable("thermostat_state") == "HEAT":
                _thermostat_state = 1
            elif self.get_variable("thermostat_state") == "COOL":
                _thermostat_state = 2
            else:
                _thermostat_state = 3
            content = {
                "thermostat_state": {
                    "Readings": [[mytime, float(_thermostat_state)]],
                    "Units": "N/A",
                    "data_type": "double"
                }
            }
            print("{} published thermostat_state to an IEB".format(agent_id))
            self.publish(_topic_Agent_sMAP, headers, json.dumps(content))

        def publish_logdata7(self):
            headers = {
                headers_mod.FROM: agent_id,
                headers_mod.CONTENT_TYPE: headers_mod.CONTENT_TYPE.JSON,
            }
            mytime = int(time.time())
            if self.get_variable("fan_state") == "OFF":
                _fan_state = 0
            elif self.get_variable("fan_state") == "ON":
                _fan_state = 1
            else:
                _fan_state = 2
            content = {
                "fan_state": {
                    "Readings": [[mytime, float(_fan_state)]],
                    "Units": "N/A",
                    "data_type": "double"
                }
            }
            print("{} published fan_state to an IEB".format(agent_id))
            self.publish(_topic_Agent_sMAP, headers, json.dumps(content))

        @matching.match_exact('/ui/agent/'+_topic_Agent_UI+'add_notification_event')
        def add_notification_event(self, topic, headers, message, match):
            print agent_id + " got\nTopic: {topic}".format(topic=topic)
            print "Headers: {headers}".format(headers=headers)
            print "Message: {message}".format(message=message)
            #reply message
            topic = '/agent/ui/'+_topic_Agent_UI+'add_notification_event/response'
            # now = datetime.utcnow().isoformat(' ') + 'Z'
            headers = {
                'AgentID': agent_id,
                headers_mod.CONTENT_TYPE: headers_mod.CONTENT_TYPE.JSON,
                # headers_mod.DATE: now,
                headers_mod.FROM: agent_id,
                headers_mod.TO: 'ui'
            }
            #add event_id to self.event_ids
            _data = json.loads(message[0])
            event_id = _data['event_id']
            print "{} added notification event_id: {}".format(agent_id, event_id)
            self.event_ids.append(event_id)
            _data = "success"
            message = _data
            # message = json.dumps(_data)
            # message = message.encode(encoding='utf_8')
            self.publish(topic, headers, message)

        @matching.match_exact('/ui/agent/'+_topic_Agent_UI+'remove_notification_event')
        def remove_notification_event(self, topic, headers, message, match):
            print agent_id + " got\nTopic: {topic}".format(topic=topic)
            print "Headers: {headers}".format(headers=headers)
            print "Message: {message}".format(message=message)
            #reply message
            topic = '/agent/ui/'+_topic_Agent_UI+'remove_notification_event/response'
            # now = datetime.utcnow().isoformat(' ') + 'Z'
            headers = {
                'AgentID': agent_id,
                headers_mod.CONTENT_TYPE: headers_mod.CONTENT_TYPE.JSON,
                # headers_mod.DATE: now,
                headers_mod.FROM: agent_id,
                headers_mod.TO: 'ui'
            }
            #add event_id to self.event_ids
            _data = json.loads(message[0])
            event_id = _data['event_id']
            print "{} removed notification event_id: {}".format(agent_id, event_id)
            self.event_ids.remove(event_id)
            _data = "success"
            message = _data
            # message = json.dumps(_data)
            # message = message.encode(encoding='utf_8')
            self.publish(topic, headers, message)

        def track_event_send_notification(self):
            for event_id in self.event_ids:
                print "{} is monitoring event_id: {}\n".format(agent_id, event_id)
                # collect information about event from notification_event table
                self.cur.execute("SELECT event_name, notify_device_id, triggered_parameter, comparator,"
                                 "threshold, notify_channel, notify_address, notify_heartbeat  FROM "
                                 + db_table_notification_event + " WHERE event_id=%s", (event_id,))
                if self.cur.rowcount != 0:
                    row = self.cur.fetchone()
                    event_name = str(row[0])
                    notify_device_id = str(row[1])
                    triggered_parameter = str(row[2])
                    comparator = str(row[3])
                    threshold = row[4]
                    notify_channel = str(row[5])
                    notify_address = row[6]
                    notify_heartbeat = row[7] if row[7] is not None else self.notify_heartbeat
                    _event_has_triggered = False
                    print "{} triggered_parameter:{} self.get_variable(triggered_parameter):{} comparator:{} threshold:{}"\
                        .format(agent_id, triggered_parameter, self.get_variable(triggered_parameter), comparator, threshold)
                    #check whether message is already sent
                    try:
                        if (datetime.datetime.now() - self.time_sent_notifications[
                            event_id]).seconds > notify_heartbeat:
                            if notify_device_id == agent_id:
                                if comparator == "<":
                                    threshold = float(threshold)
                                    if self.get_variable(triggered_parameter) < threshold: _event_has_triggered = True
                                elif comparator == ">":
                                    threshold = float(threshold)
                                    if self.get_variable(triggered_parameter) > threshold: _event_has_triggered = True
                                    print "{} triggered_parameter:{} self.get_variable(triggered_parameter):{} comparator:{} threshold:{}"\
                                        .format(agent_id, triggered_parameter, self.get_variable(triggered_parameter), comparator, threshold)
                                    print "{} _event_has_triggerered {}".format(agent_id,_event_has_triggered)
                                elif comparator == "<=":
                                    threshold = float(threshold)
                                    if self.get_variable(triggered_parameter) <= threshold: _event_has_triggered = True
                                elif comparator == ">=":
                                    threshold = float(threshold)
                                    if self.get_variable(triggered_parameter) >= threshold: _event_has_triggered = True
                                elif comparator == "is":
                                    if threshold == "True":
                                        threshold = True
                                    elif threshold == "False":
                                        threshold = False
                                    else:
                                        threshold = str(threshold)
                                    if self.get_variable(triggered_parameter) is threshold: _event_has_triggered = True
                                elif comparator == "isnot":
                                    if threshold == "True":
                                        threshold = True
                                    elif threshold == "False":
                                        threshold = False
                                    else:
                                        threshold = str(threshold)
                                    if self.get_variable(
                                            triggered_parameter) is not threshold: _event_has_triggered = True
                                else:
                                    pass
                                if _event_has_triggered:  # notify the user if triggered
                                    #step2 notify user to notify_channel at notify_address with period notify_heartbeat
                                    if notify_channel == 'email':
                                        _email_text = '{} notification event triggered_parameter: {}, comparator: {}, ' \
                                                      'threshold: {}\n now the current status of triggered_parameter: {} is {}' \
                                            .format(agent_id, triggered_parameter, comparator, threshold,
                                                    triggered_parameter, self.get_variable(triggered_parameter))
                                        emailService = EmailService()
                                        emailService.sendEmail(email_fromaddr, notify_address, email_username,
                                                               email_password,
                                                               self.subject, _email_text, email_mailServer)
                                        # self.send_notification_status = True
                                        #TODO store time_send_notification for each event
                                        self.time_sent_notifications[event_id] = datetime.datetime.now()
                                        print "time_sent_notifications is {}".format(
                                            self.time_sent_notifications[event_id])
                                        print('{} >> sent notification message for {}'.format(agent_id, event_name))
                                        print(
                                        '{} notification event triggered_parameter: {}, comparator: {}, threshold: {}'
                                        .format(agent_id, triggered_parameter, comparator, threshold))
                                    else:
                                        print "{} >> notification channel: {} is not supported yet".format(agent_id,
                                                                                                           notify_channel)
                                else:
                                    print "{} >> Event is not triggered".format(agent_id)
                            else:
                                "{} >> this event_id {} is not for this device".format(agent_id, event_id)
                        else:
                            "{} >> Email is already sent, waiting for another heartbeat period".format(agent_id)
                    except:
                        #step1 compare triggered_parameter with comparator to threshold
                        #step1.1 classify comparator <,>,<=,>=,is,isnot
                        #case1 comparator <
                        print "{} >> first time trigger notification".format(agent_id)
                        if notify_device_id == agent_id:
                            if comparator == "<":
                                threshold = float(threshold)
                                if self.get_variable(triggered_parameter) < threshold: _event_has_triggered = True
                            elif comparator == ">":
                                threshold = float(threshold)
                                if self.get_variable(triggered_parameter) > threshold: _event_has_triggered = True
                                print "{} triggered_parameter:{} self.get_variable(triggered_parameter):{} comparator:{} threshold:{}"\
                                        .format(agent_id, triggered_parameter, self.get_variable(triggered_parameter), comparator, threshold)
                                print "{} _event_has_triggerered {}".format(agent_id,_event_has_triggered)
                            elif comparator == "<=":
                                threshold = float(threshold)
                                if self.get_variable(triggered_parameter) <= threshold: _event_has_triggered = True
                            elif comparator == ">=":
                                threshold = float(threshold)
                                if self.get_variable(triggered_parameter) >= threshold: _event_has_triggered = True
                            elif comparator == "is":
                                if threshold == "True":
                                    threshold = True
                                elif threshold == "False":
                                    threshold = False
                                else:
                                    threshold = str(threshold)
                                if self.get_variable(triggered_parameter) is threshold: _event_has_triggered = True
                            elif comparator == "isnot":
                                if threshold == "True":
                                    threshold = True
                                elif threshold == "False":
                                    threshold = False
                                else:
                                    threshold = str(threshold)
                                if self.get_variable(triggered_parameter) is not threshold: _event_has_triggered = True
                            else:
                                pass
                            print "{} >> _event_has_triggered {}".format(agent_id, _event_has_triggered)
                            if _event_has_triggered:  # notify the user if triggered
                                #step2 notify user to notify_channel at notify_address with period notify_heartbeat
                                if notify_channel == 'email':
                                    _email_text = '{} notification event triggered_parameter: {}, comparator: {}, ' \
                                                  'threshold: {}\n now the current status of triggered_parameter: {} is {}' \
                                        .format(agent_id, triggered_parameter, comparator, threshold,
                                                triggered_parameter, self.get_variable(triggered_parameter))
                                    emailService = EmailService()
                                    emailService.sendEmail(email_fromaddr, notify_address, email_username,
                                                           email_password,
                                                           self.subject, _email_text, email_mailServer)
                                    # self.send_notification_status = True
                                    #store time_send_notification for each event
                                    self.time_sent_notifications[event_id] = datetime.datetime.now()
                                    print "{} >> time_sent_notifications is {}".format(agent_id, self.time_sent_notifications[event_id])
                                    print('{} >> sent notification message for {}'.format(agent_id, event_name))
                                    print('{} notification event triggered_parameter: {}, comparator: {}, threshold: {}'
                                          .format(agent_id, triggered_parameter, comparator, threshold))
                                else:
                                    print "{} >> notification channel: {} is not supported yet".format(agent_id,
                                                                                                       notify_channel)
                            else:
                                print "{} >> Event is not triggered".format(agent_id)
                        else:
                            "{} >> this event_id {} is not for this device".format(agent_id, event_id)
                else:
                    pass

    Agent.__name__ = 'Thermostat Agent'
    return Agent(**kwargs)

def main(argv=sys.argv):
    '''Main method called by the eggsecutable.'''
    utils.default_main(ThermostatAgent,
                       description='Thermostat agent',
                       argv=argv)

if __name__ == '__main__':
    # Entry point for script
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        pass
