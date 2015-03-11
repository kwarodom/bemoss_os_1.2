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
__credits__ = "Avijit saha"
__version__ = "1.2.1"
__maintainer__ = "Warodom Khamphanchai"
__email__ = "kwarodom@vt.edu"
__website__ = "kwarodom.wordpress.com"
__status__ = "Prototype"
__created__ = "2014-7-28 10:20:00"
__lastUpdated__ = "2015-02-11 16:43:00"
'''

import sys
import json
import time
import logging
import importlib
from volttron.lite.agent import BaseAgent, PublishMixin, periodic
from volttron.lite.agent import utils, matching
from volttron.lite.messaging import headers as headers_mod
import datetime
from bemoss.communication.Email import EmailService
import psycopg2
import psycopg2.extras
import socket
import settings

utils.setup_logging()
_log = logging.getLogger(__name__)

#Step1: Agent Initialization
def LightingAgent(config_path, **kwargs):
    config = utils.load_config(config_path)

    def get_config(name):
        try:
            value = kwargs.pop(name)
        except KeyError:
            return config.get(name, '')

    #1. @params agent
    agent_id = get_config('agent_id')
    # LOG_DATA_PERIOD = get_config('poll_time')
    device_monitor_time = get_config('device_monitor_time')
    publish_address = 'ipc:///tmp/volttron-lite-agent-publish'
    subscribe_address = 'ipc:///tmp/volttron-lite-agent-subscribe'
    debug_agent = False
    #List of all keywords for a lighting agent
    agentknowledge = dict(status=["status", "on", "off", "ON", "OFF"], brightness=["brightness", "bri"],
                          color=["color"], saturation=["saturation", "sat"])
    agentAPImapping = dict(status=[], brightness=[], color=[], saturation=[])

    #2. @params device_info
    #TODO correct the launchfile in Device Discovery Agent
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

    #3. @params agent & DB interfaces
    #TODO delete variable topic
    topic = get_config('topic')

    #TODO get database parameters from settings.py, add db_table for specific table
    db_host = get_config('db_host')
    db_port = get_config('db_port')
    db_database = get_config('db_database')
    db_user = get_config('db_user')
    db_password = get_config('db_password')
    db_table_lighting = settings.DATABASES['default']['TABLE_lighting']
    db_table_notification_event = settings.DATABASES['default']['TABLE_notification_event']

    #TODO construct _topic_Agent_UI based on data obtained from DB
    _topic_Agent_UI = building_name+'/'+str(zone_id)+'/'+device_type+'/'+agent_id + '/'
    # _topic_Agent_UI = 'building1/999/'+device_type+'/'+agent_id+'/'
    # print(_topic_Agent_UI)

    #TODO construct _topic_Agent_sMAP based on data obtained from DB
    # _topic_Agent_sMAP = 'datalogger/log/building1/999/'+device_type+'/'+agent_id
    _topic_Agent_sMAP = 'datalogger/log/'+building_name+'/'+str(zone_id)+'/'+device_type+'/'+agent_id
    # print(_topic_Agent_sMAP)

    #4. @params device_api
    api = get_config('api')
    #TODO discovery agent locate the location of api in launch file e.g. "api": "testAPI.classAPI_RadioThermostat",
    # apiLib = importlib.import_module(api)
    # print(apiLib)
    apiLib = importlib.import_module("testAPI."+api)
    print("testAPI."+api)

    #4.1 initialize thermostat device object
    Light = apiLib.API(model=model, device_type=device_type, api=api, address=address, agent_id=agent_id)
    print("{0}agent is initialized for {1} using API={2} at {3}".format(agent_id, Light.get_variable('model'),
                                                                        Light.get_variable('api'),
                                                                        Light.get_variable('address')))

    #4.2 initialize values of a Lighting

    #5. @params notification_info
    send_notification = True
    email_fromaddr = settings.NOTIFICATION['email']['fromaddr']
    email_recipients = settings.NOTIFICATION['email']['recipients']
    email_username = settings.NOTIFICATION['email']['username']
    email_password = settings.NOTIFICATION['email']['password']
    email_mailServer = settings.NOTIFICATION['email']['mailServer']
    notify_heartbeat = settings.NOTIFICATION['heartbeat']
    alert_too_dark = settings.NOTIFICATION['lighting']['too_dark']

    class Agent(PublishMixin, BaseAgent):
        """Agent for querying WeatherUndergrounds API"""

        #1. agent initialization    
        def __init__(self, **kwargs):
            super(Agent, self).__init__(**kwargs)
            #1. initialize all agent variables
            self.variables = kwargs
            self.valid_data = False
            self._keep_alive = True
            self.flag = 1
            self.topic = topic
            self.time_send_notification = 0
            self.event_ids = list()
            self.time_sent_notifications = {}
            self.notify_heartbeat = notify_heartbeat
            self.ip_address = ip_address if ip_address != None else None
            #2. setup connection with db -> Connect to bemossdb database
            try:
                self.con = psycopg2.connect(host=db_host, port=db_port, database=db_database, user=db_user,
                                            password=db_password)
                self.cur = self.con.cursor()  # open a cursor to perfomm database operations
                print("{} connects to the database name {} successfully".format(agent_id, db_database))
            except:
                print("ERROR: {} fails to connect to the database name {}".format(agent_id, db_database))
            #3. send notification to notify building admin
            self.send_notification = send_notification
            # if self.send_notification:
            self.subject = 'Message from ' + agent_id
            #     self.text = 'Now an agent device_type {} for {} with API {} at address {} is launched!'.format(
            #         Light.get_variable('device_type'), Light.get_variable('model'),
            #         Light.get_variable('api'), Light.get_variable('address'))
            #     emailService = EmailService()
            #     emailService.sendEmail(email_fromaddr, email_recipients, email_username, email_password, self.subject,
            #                            self.text, email_mailServer)

        #These set and get methods allow scalability 
        def set_variable(self,k,v):  # k=key, v=value
            self.variables[k] = v
    
        def get_variable(self,k):
            return self.variables.get(k, None)  # default of get_variable is none
        
        #2. agent setup method
        def setup(self):
            super(Agent, self).setup()
            #Do a one time push when we start up so we don't have to wait for the periodic
            self.timer(1, self.deviceMonitorBehavior)
            if identifiable == "True": Light.identifyDevice()
            # Light.setDeviceStatus({"status": "ON", "brightness": 100, "color": (255, 0, 0), "saturation": 80})

        #3. deviceMonitorBehavior (TickerBehavior)
        @periodic(device_monitor_time) 
        def deviceMonitorBehavior(self):
            #step1: get current status of a thermostat, then map keywords and variables to agent knowledge
            try:
                Light.getDeviceStatus()
                #mapping variables from API to Agent's knowledge
                for APIKeyword, APIvariable in Light.variables.items():
                    if debug_agent:
                        print (APIKeyword, APIvariable)
                    self.set_variable(self.getKeyword(APIKeyword), APIvariable)  # set variables of agent from API variables
                    agentAPImapping[self.getKeyword(APIKeyword)] = APIKeyword  # map keyword of agent and API
            except:
                print("device connection is not successful")

            #step3: send notification to a user if required
            if self.send_notification:
                self.track_event_send_notification()

            #step4: update PostgresQL (meta-data) database
            #TODO last_scanned_time
            _time_stamp_last_scanned = datetime.datetime.now()
            self.cur.execute("UPDATE "+db_table_lighting+" SET last_scanned_time=%s "
                             "WHERE lighting_id=%s",
                             (_time_stamp_last_scanned, agent_id))
            self.con.commit()
            #TODO last_offline_time FIXXXXX
            # _time_stamp_last_offline = datetime.datetime.now()
            # self.cur.execute("UPDATE "+db_table_lighting+" SET last_offline_time=%s "
            #                  "WHERE lighting_id=%s",
            #                  (_time_stamp_last_offline, agent_id))
            # self.con.commit()
            try:
                self.cur.execute("UPDATE "+db_table_lighting+" SET status=%s WHERE lighting_id=%s",
                                 (self.get_variable('status'), agent_id))
                self.con.commit()
                self.cur.execute("UPDATE "+db_table_lighting+" SET brightness=%s WHERE lighting_id=%s",
                                 (self.get_variable('brightness'), agent_id))
                self.con.commit()
                self.cur.execute("UPDATE "+db_table_lighting+" SET color=%s WHERE lighting_id=%s",
                                 (self.get_variable('color'), agent_id))
                self.con.commit()
                if self.get_variable('status') == "ON":
                    multiple_on_off_status = ""
                    for dummyvar in range(self.get_variable('number_lights')):
                        multiple_on_off_status += "1"
                    self.cur.execute("UPDATE "+db_table_lighting+" SET multiple_on_off=%s WHERE lighting_id=%s",
                                    (multiple_on_off_status, agent_id))
                    self.con.commit()
                else:  # status is off
                    multiple_on_off_status = ""
                    for dummyvar in range(self.get_variable('number_lights')):
                        multiple_on_off_status += "0"
                    self.cur.execute("UPDATE "+db_table_lighting+" SET multiple_on_off=%s WHERE lighting_id=%s",
                                    (multiple_on_off_status, agent_id))
                    self.con.commit()
                #TODO check ip_address
                if self.ip_address != None:
                    psycopg2.extras.register_inet()
                    _ip_address = psycopg2.extras.Inet(self.ip_address)
                    self.cur.execute("UPDATE "+db_table_lighting+" SET ip_address=%s WHERE lighting_id=%s",
                                     (_ip_address, agent_id))
                    self.con.commit()
                #TODO check nickname
                #TODO check zone_id
                #TODO check network_status
                #TODO check other_parameters
                #TODO last_scanned_time
                _time_stamp_last_scanned = datetime.datetime.now()
                self.cur.execute("UPDATE "+db_table_lighting+" SET last_scanned_time=%s "
                                 "WHERE lighting_id=%s",
                                 (_time_stamp_last_scanned, agent_id))
                self.con.commit()
                #TODO last_offline_time FIXXXXX
                # _time_stamp_last_offline = datetime.datetime.now()
                # self.cur.execute("UPDATE "+db_table_lighting+" SET last_offline_time=%s "
                #                  "WHERE lighting_id=%s",
                #                  (_time_stamp_last_offline, agent_id))
                # self.con.commit()
                print("{} updates database name {} during deviceMonitorBehavior successfully".format(agent_id, db_database))
            except:
                print("ERROR: {} fails to update the database name {}".format(agent_id,db_database))

            #step5: update sMAP (time-series) database
            try:
                self.publish_logdata1()
                if self.get_variable('brightness') is not None:
                    self.publish_logdata2()
                if self.get_variable('hue') is not None:
                    self.publish_logdata3()
                if self.get_variable('saturation') is not None:
                    self.publish_logdata4()
                print "success update sMAP database"
            except:
                print("ERROR: {} fails to update sMAP database".format(agent_id))

            #step6: debug agent knowledge
            if debug_agent:
                print("printing agent's knowledge")
                for k,v in self.variables.items():
                    print (k,v)
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
            if flag == 0: #if flag still 0 means that a APIKeyword is not in an agent knowledge, then add it to agent knowledge
                return APIKeyword
        
        #4. updateUIBehavior (generic behavior)
        @matching.match_exact('/ui/agent/'+_topic_Agent_UI+'device_status')
        def updateUIBehavior(self,topic,headers,message,match):
            print "{} agent got\nTopic: {topic}".format(self.get_variable("agent_id"),topic=topic)
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
            _data={'status': self.get_variable('status'),
                   'brightness': self.get_variable('brightness'), 'color': self.get_variable('color'),
                   'saturation': self.get_variable('saturation')}
            message = json.dumps(_data) 
            message = message.encode(encoding='utf_8')
            self.publish(topic, headers, message)

        #5. deviceControlBehavior (generic behavior)
        @matching.match_exact('/ui/agent/'+_topic_Agent_UI+'update')
        def deviceControlBehavior(self,topic,headers,message,match):
            print "{} agent got\nTopic: {topic}".format(self.get_variable("agent_id"),topic=topic)
            print "Headers: {headers}".format(headers=headers)
            print "Message: {message}\n".format(message=message)
            #step1: change dev
            # ice status according to the receive message
            if self.isPostmsgValid(message[0]):
                setDeviceStatusResult = Light.setDeviceStatus(json.loads(message[0])) #convert received message from string to JSON
                #TODO need to do additional checking whether the device setting is actually success!!!!!!!!
                #step2: update agent's knowledge on this device
                Light.getDeviceStatus()
                #step3: send reply message back to the UI
                topic = '/agent/ui/'+_topic_Agent_UI+'update/response'
                # now = datetime.utcnow().isoformat(' ') + 'Z'
                headers = {
                    'AgentID': agent_id,
                    headers_mod.CONTENT_TYPE: headers_mod.CONTENT_TYPE.PLAIN_TEXT,
                    # headers_mod.DATE: now,
                    headers_mod.FROM: agent_id,
                    headers_mod.TO: 'ui'
                }
                if setDeviceStatusResult:
                    message = 'success'
                else:
                    message = 'failure'
            else:
                print("The POST message is invalid, check thermostat_mode, heat_setpoint, cool_coolsetpoint "
                      "setting and try again\n")
                message = 'failure'
            self.publish(topic, headers, message)

        def isPostmsgValid(self, postmsg):  # check validity of postmsg
            dataValidity = True
            try:
                _data = json.dumps(postmsg)
                _data = json.loads(_data)
                for k, v in _data.items():
                    if k == 'color':
                        if type(_data.get('color')) == tuple|list:
                            dataValidity = True
            except:
                dataValidity = True
                print("dataValidity failed to validate data comes from UI")
            return dataValidity

        #6. deviceIdentifyBehavior (generic behavior)
        @matching.match_exact('/ui/agent/'+_topic_Agent_UI+'identify')
        def deviceIdentifyBehavior(self,topic,headers,message,match):
            print "{} agent got\nTopic: {topic}".format(self.get_variable("agent_id"),topic=topic)
            print "Headers: {headers}".format(headers=headers)
            print "Message: {message}\n".format(message=message)
            #step1: change device status according to the receive message
            identifyDeviceResult = Light.identifyDevice()
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

        #7. Update data to sMAP
        def publish_logdata1(self):
            headers = {
                headers_mod.FROM: agent_id,
                headers_mod.CONTENT_TYPE: headers_mod.CONTENT_TYPE.JSON,
            }
            mytime = int(time.time())
            content = {
            "status": {
                    "Readings": [[mytime, float(1 if self.get_variable("status") == "ON" else 0)]],
                    "Units": "N/A",
                    "data_type": "double"
                }
            }
            print("{} published status to an IEB".format(agent_id))
            self.publish(_topic_Agent_sMAP, headers, json.dumps(content))

        def publish_logdata2(self):
            headers = {
                headers_mod.FROM: agent_id,
                headers_mod.CONTENT_TYPE: headers_mod.CONTENT_TYPE.JSON,
            }
            mytime = int(time.time())
            content = {
                "brightness": {
                        "Readings": [[mytime, float(self.get_variable("brightness"))]],
                        "Units": "%",
                        "data_type": "double"
                    }
            }
            print("{} published brightness to an IEB".format(agent_id))
            self.publish(_topic_Agent_sMAP, headers, json.dumps(content))

        def publish_logdata3(self):
            headers = {
                headers_mod.FROM: agent_id,
                headers_mod.CONTENT_TYPE: headers_mod.CONTENT_TYPE.JSON,
            }
            mytime = int(time.time())
            content = {
            "hue": {
                    "Readings": [[mytime, float(self.get_variable("hue"))]],
                    "Units": "hue",
                    "data_type": "double"
                }
            }
            print("{} published hue to an IEB".format(agent_id))
            self.publish(_topic_Agent_sMAP, headers, json.dumps(content))

        def publish_logdata4(self):
            headers = {
                headers_mod.FROM: agent_id,
                headers_mod.CONTENT_TYPE: headers_mod.CONTENT_TYPE.JSON,
            }
            mytime = int(time.time())
            content = {
            "saturation": {
                    "Readings": [[mytime, float(self.get_variable("saturation"))]],
                    "Units": "%",
                    "data_type": "double"
                }
            }
            print("{} published saturation to an IEB".format(agent_id))
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

    Agent.__name__ = 'LightingAgent'
    return Agent(**kwargs)

def main(argv=sys.argv):
    '''Main method called by the eggsecutable.'''
    utils.default_main(LightingAgent,
                       description='Lighting agent',
                       argv=argv)

if __name__ == '__main__':
    # Entry point for script
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        pass
