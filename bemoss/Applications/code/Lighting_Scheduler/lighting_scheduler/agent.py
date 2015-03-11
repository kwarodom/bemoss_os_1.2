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
__lastUpdated__ = "2015-02-11 17:17:33"
'''

import sys
import json
import logging
from volttron.lite.agent import BaseAgent, PublishMixin, periodic
from volttron.lite.agent import utils, matching
from volttron.lite.messaging import headers as headers_mod
import psycopg2  # PostgresQL database adapter
import time
import datetime
import settings
import re
import pprint

utils.setup_logging()
_log = logging.getLogger(__name__)

# Step1: Agent Configuration
def scheduleragent(config_path, **kwargs):
    config = utils.load_config(config_path)

    def get_config(name):
        try:
            kwargs.pop(name)
        except KeyError:
            return config.get(name, '')

    # 1. define name of this application
    app_name = "lighting_scheduler"

    # 2. @params agent
    agent_id = get_config('agent_id')
    clock_time = 1  # schedule is updated every second
    publish_address = 'ipc:///tmp/volttron-lite-agent-publish'
    subscribe_address = 'ipc:///tmp/volttron-lite-agent-subscribe'
    debug_agent = False
    device_type = 'lighting'

    # 3. @params DB interfaces (settings file in ~/workspace/bemoss_os/)
    # 3.1 PostgreSQL (meta-data database) connection information
    db_host = settings.DATABASES['default']['HOST']
    db_port = settings.DATABASES['default']['PORT']
    db_database = settings.DATABASES['default']['NAME']
    db_user = settings.DATABASES['default']['USER']
    db_password = settings.DATABASES['default']['PASSWORD']
    db_table_application_registered = settings.DATABASES['default']['TABLE_application_registered']
    db_table_application_running = settings.DATABASES['default']['TABLE_application_running']

    # 3.2 sMAP (time-series data database) connection information
    # construct topic_app_sMAP based on data obtained from the launcher
    _topic_Agent_sMAP = 'datalogger/log/' + app_name + agent_id + '/'

    # 4. set exchanged topics between this app and other entities
    # 4.1 exchanged topic app and agent
    # construct topic_app_agent based on data obtained from the launcher
    topic_app_agent = '/ui/agent/building1/999/'+device_type+'/'+agent_id+'/'+'update'
    topic_agent_app = '/agent/ui/building1/999/'+device_type+'/'+agent_id+'/'+'update/response'

    # 4.2 exchanged topic ui and app
    # construct topic_ui_app based on data obtained from the launcher
    topic_ui_app = '/ui/app/' + app_name + '/' + agent_id + '/' + 'update'
    topic_app_ui = '/app/ui/' + app_name + '/' + agent_id + '/' + 'update/response'

    class Agent(PublishMixin, BaseAgent):

        # 1. agent initialization
        def __init__(self, **kwargs):
            super(Agent, self).__init__(**kwargs)
            # 1. initialize all agent variables
            self.variables = kwargs
            # self.timeModeTemp = kwargs
            # self.timeModeTemp.clear()
            self.timeStatusBrightnessColor = kwargs
            self.timeStatusBrightnessColor.clear()
            self.flag_time_to_change_status = False
            self.current_use_schedule = None
            self.schedule_first_run = False
            self.old_day = self.find_day()
            self.active_scheduler_mode = list()
            self.time_next_schedule_sec = int(24*3600)
            self.weekday_list = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']
            self.weekend_list = ['saturday', 'sunday']
            self.current_schedule_object = None
            # 2. connect to the database
            try:
                self.con = psycopg2.connect(host=db_host, port=db_port, database=db_database, user=db_user,
                                            password=db_password)
                self.cur = self.con.cursor()  # open a cursor to perfomm database operations
                print("{} for Agent: {} >> connects to the database name {} successfully"
                      .format(app_name, agent_id, db_database))
            except:
                print("ERROR: {} for Agent: {} >> fails to connect to the database name {}"
                      .format(app_name, agent_id, db_database))

            try:
                app_agent_id = app_name+'_'+agent_id
                self.cur.execute("SELECT app_setting FROM application_running WHERE app_agent_id=%s", (app_agent_id,))
                if self.cur.rowcount != 0:
                    _launch_file = str(self.cur.fetchone()[0])
                    with open(_launch_file) as json_data:
                        _new_schedule_object = json.load(json_data)
                    # pprint(_new_schedule_object)
                    # print '_launch_file' + _launch_file
                    # set self.current_schedule_object to be the new schedule
                    self.current_schedule_object = _new_schedule_object['lighting']
                    #3. get currently active schedule
                    self.active_scheduler_mode = list()
                    print '{} for Agent: {} >> new active schedule are as follows:'.format(app_name, agent_id)
                    for each1 in self.current_schedule_object[agent_id]:
                        if each1 == 'active':
                            for each2 in self.current_schedule_object[agent_id][each1]:
                                self.active_scheduler_mode.append(each2)

                    for index in range(len(self.active_scheduler_mode)):
                        print "- " + self.active_scheduler_mode[index]

                    #4. RESTART Scheduler Agent **************** IMPORTANT
                    self.set_query_mode_all_day()
                    self.schedule_first_run = True
                    #******************************************* IMPORTANT
                    print("{} for Agent: {} >> DONE getting data from applications_running".format(app_name, agent_id))
                else:
                    print("{} for Agent: {} >> has no previous setting before".format(app_name, agent_id))
            except:
                print("{} for Agent: {} >> error getting data from applications_running"
                      .format(app_name, agent_id))

        #2. agent setup method
        def setup(self):
            super(Agent, self).setup()
            print "{} for Agent: {} >> has been launched successfully".format(app_name, agent_id)
            print "{} for Agent: {} >> is waiting to be configured by the setting sent from the UI"\
                .format(app_name, agent_id)

        # 3. clockBehavior (CyclicBehavior)
        @periodic(clock_time)
        def clockBehavior(self):
            # 1. check current time
            self.htime = datetime.datetime.now().hour
            self.mtime = datetime.datetime.now().minute
            self.stime = datetime.datetime.now().second
            self.now_decimal = int(self.htime)*60 + int(self.mtime)
            self.time_now_sec = int(self.htime*3600) + int(self.mtime)*60 + int(self.stime)

            # 2. update self.schedule_first_run to True if day has change
            self.new_day = self.find_day()
            if self.new_day != self.old_day:
                if self.current_schedule_object != None:
                    #RESTART Scheduler Agent ******************* IMPORTANT
                    self.set_query_mode_all_day()
                    self.schedule_first_run = True
                    self.old_day = self.new_day
                    #******************************************* IMPORTANT
                    print '{} for Agent: {} >> today: {} is  a new day (yesterday: {}), load new schedule for today'\
                        .format(app_name, agent_id, self.new_day, self.old_day)
                else:
                    print '{} for Agent: {} >> today: {} is  a new day (yesterday: {}), but no schedule has been set yet'\
                        .format(app_name, agent_id, self.new_day, self.old_day)
            else: # same day no reset is required
                pass

            # 3. self.schedule_first_run to True is triggered by 1. setting from UI or 2. Day change
            if self.schedule_first_run is True:
                self.schedule_action()
                self.schedule_first_run = False
            else:
                pass

            # 4. if next schedule comes up, run self.schedule_action()
            if self.time_now_sec >= self.time_next_schedule_sec:
                if debug_agent: print "{} for Agent: >> {} now _time_now_sec= {}, self.time_next_schedule_sec ={}"\
                    .format(app_name, agent_id, self.time_now_sec, self.time_next_schedule_sec)
                print "{} for Agent: {} >> is now woken up".format(app_name, agent_id)
                self.schedule_action()

        # 4. updateScheduleBehavior (GenericBehavior)
        @matching.match_exact(topic_ui_app)
        def updateScheduleBehavior(self, topic, headers, message, match):
            # print agent_id + " got\nTopic: {topic}".format(topic=topic)
            # print "Headers: {headers}".format(headers=headers)
            # print "Message: {message}\n".format(message=message)
            # take action to update new schedule to an agent
            _time_receive_update_from_ui = datetime.datetime.now()
            print "{} for Agent: {} >> got new update from UI at {}".format(app_name, agent_id,
                                                                            _time_receive_update_from_ui)
            # 1. get path to the new launch file from the message sent by UI
            # _data = json.dumps(message[0])
            try:
                _data = json.loads(message[0])
                _launch_file = _data.get('path')
                print '{} for Agent: {} >> new schedule path is at: {}'.format(app_name, agent_id, _launch_file)
                app_agent_id = app_name + "_" + agent_id
                print "app_agent_id = {}".format(app_agent_id)
                self.cur.execute("UPDATE application_running SET app_setting=%s WHERE app_agent_id=%s"
                                 , (_launch_file, app_agent_id))
                self.con.commit()
                print '{} for Agent: {} >> DONE update applications_running table with path {}'\
                    .format(app_name, agent_id, _launch_file)

                # 2. load new schedule from the new launch file
                with open(_launch_file) as json_data:
                    _new_schedule_object = json.load(json_data)
                # pprint(_new_schedule_object)
                # set self.current_schedule_object to be the new schedule
                self.current_schedule_object = _new_schedule_object['lighting']

                # 3. get currently active schedule
                self.active_scheduler_mode = list()
                print '{} for Agent: {} >> new active schedule are as follows:'.format(app_name, agent_id)
                for each1 in self.current_schedule_object[agent_id]:
                    if each1 == 'active':
                        for each2 in self.current_schedule_object[agent_id][each1]:
                            self.active_scheduler_mode.append(each2)

                for index in range(len(self.active_scheduler_mode)):
                    print "- " + self.active_scheduler_mode[index]

                # 4. RESTART Scheduler Agent **************** IMPORTANT
                self.set_query_mode_all_day()
                self.schedule_first_run = True
                #******************************************* IMPORTANT

                # reply message from app to ui
                _headers = {
                    'AppName': app_name,
                    'AgentID': agent_id,
                    headers_mod.CONTENT_TYPE: headers_mod.CONTENT_TYPE.JSON,
                    headers_mod.FROM: agent_id,
                    headers_mod.TO: 'ui'
                }
                _message = 'success'
                self.publish(topic_app_ui, _headers, _message)
                print '{} for Agent: {} >> DONE update new active schedule received from UI'\
                    .format(app_name, agent_id)
            except:
                print "{} for Agent: {} >> ERROR update new schedule received from UI at {}"\
                    .format(app_name, agent_id, _time_receive_update_from_ui)
                print "{} for Agent: {} >> possible ERRORS are as follows: "\
                    .format(app_name, agent_id, _time_receive_update_from_ui)
                print "{} for Agent: {} >> ERROR 1 : path to update schedule sent by UI is incorrect "\
                    .format(app_name, agent_id, _time_receive_update_from_ui)
                print "{} for Agent: {} >> ERROR 2 : content inside schedule setting file (JSON) sent by UI" \
                      " is incorrect ".format(app_name, agent_id, _time_receive_update_from_ui)

        # Helper methods --------------------------------------
        def set_query_mode_all_day(self):
            if 'holiday' in self.active_scheduler_mode:
                # 1. find whether today is a holiday by query db 'public.holiday'
                _date_today = str(datetime.datetime.now().date())
                self.cur.execute("SELECT description FROM holiday WHERE date=%s", (_date_today,))
                if self.cur.rowcount != 0:
                    self.holiday_description = self.cur.fetchone()[0]
                    print '---------------------------------'
                    print "{} for Agent: {} >> Hoorey! today is a holiday: {}"\
                        .format(app_name, agent_id, self.holiday_description)
                    self.todayHoliday = True
                else:
                    print '---------------------------------'
                    print "{} for Agent: {} >> Today is not a holiday".format(app_name, agent_id)
                    self.todayHoliday = False

                # 2. select schedule according to the day
                if self.todayHoliday is True:
                    self.today = self.find_day()
                    print "{} for Agent: {} >> mode: holiday".format(app_name, agent_id)
                    self.query_schedule_mode = 'holiday'
                    self.query_schedule_point = 'holiday'
                    self.get_schedule_time_status_brightness_color()
                else:
                    self.set_query_mode_point_everyday_weekdayweekend()
                    self.get_schedule_time_status_brightness_color()
            else:  # no holiday mode
                self.todayHoliday = False
                self.set_query_mode_point_everyday_weekdayweekend()
                self.get_schedule_time_status_brightness_color()
                
        def set_query_mode_point_everyday_weekdayweekend(self):
            # find the day of today then print the setting of the Scheduler Agent
            self.today = self.find_day()
            if 'everyday' in self.active_scheduler_mode:
                print '---------------------------------'
                print "{} for Agent: {} >> mode: everyday".format(app_name, agent_id)
                self.query_schedule_mode = 'everyday'
                self.query_schedule_point = self.today
            elif 'weekdayweekend' in self.active_scheduler_mode:
                print '---------------------------------'
                print '{} for Agent: {} >> mode: weekdayweekend'.format(app_name, agent_id)
                self.query_schedule_mode = 'weekdayweekend'
                # find whether today is a weekday or weekend
                if self.today in self.weekday_list:
                    self.query_schedule_point = 'weekday'
                elif self.today in self.weekend_list:
                    self.query_schedule_point = 'weekend'
                else:  #TODO change this default setting
                    self.query_schedule_point = 'weekday'

        def get_schedule_time_status_brightness_color(self):
            # 1. get time-related schedule including: 1.status 2.brightness 3.color
            self.newTimeScheduleChange = list()
            for eachtime in self.current_schedule_object[agent_id]['schedulers'][self.query_schedule_mode][self.query_schedule_point]:
                # time that scheduler need to change a light setting
                self.newTimeScheduleChange.append(int(eachtime['at']))
                # dictionary relate time with 1.status 2.brightness 3.color
                try:
                    if eachtime['status'] is not None:
                        _status_to_store = str(eachtime['status'])
                    else:
                        _status_to_store = "None"
                except:
                    _status_to_store = "None"
                try:
                    if eachtime['brightness'] is not None:
                        _brightness_to_store = str(eachtime['brightness'])
                    else:
                        _brightness_to_store = "None"
                except:
                    _brightness_to_store = "None"
                try:
                    if eachtime['color'] is not None:
                        _color_to_store = str(eachtime['color'])
                    else:
                        _color_to_store = "None"
                except:
                    _color_to_store = "None"

                self.timeStatusBrightnessColor[str(eachtime['at'])] = str(_status_to_store + "|"
                                                                          + _brightness_to_store + "|"
                                                                          + _color_to_store)

            # 2. sort time to change the schedule in ascending order
            self.newTimeScheduleChange.sort()

            # 3. get the schedule: reordered time and corresponding mode and temperature setting
            if self.todayHoliday is True:
                print "{} for Agent: {} >> Today is {} and here is the schedule for holiday:"\
                    .format(app_name, agent_id, self.holiday_description)
            else:
                if self.query_schedule_mode is 'everyday':
                    print "{} for Agent: {} >> Today is {} and here is the schedule for today:"\
                        .format(app_name, agent_id, self.today)
                elif self.query_schedule_point is 'weekday':
                    print "{} for Agent: {} >> Today is {} and here is the schedule for the weekday:"\
                        .format(app_name, agent_id, self.today)
                elif self.query_schedule_point is 'weekend':
                    print "{} for Agent: {} >> Today is {} and here is the schedule for the weekend:"\
                        .format(app_name, agent_id, self.today)
            for index in range(len(self.newTimeScheduleChange)):
                _time = self.newTimeScheduleChange[index]
                _hour = int(_time/60)
                _minute = int(_time - (_hour*60))
                _status_brightness_color = str(self.timeStatusBrightnessColor[str(self.newTimeScheduleChange[index])]).split('|')
                _status = _status_brightness_color[0]
                _brightness = _status_brightness_color[1]
                _color = _status_brightness_color[2]
                print "{} for Agent: {} >> At {} hr {} min status: {}, brightness: {}, color: {}"\
                    .format(app_name, agent_id, str(_hour), str(_minute), str(_status), str(_brightness), str(_color))
            print ''

        def schedule_action(self):
            '''before call this method make sure that self.timeStatusBrightnessColor
            and self.newTimeScheduleChange has been updated!'''
            print '{} for Agent: {} >> current time {} hr {} min {} sec (decimal = {})'\
                .format(app_name, agent_id, self.htime, self.mtime, self.stime, str(self.now_decimal))

            # 1.2 check current and past schedule
            _pastSchedule = list()  # list to save times of previous schedules 
            for index in range(len(self.newTimeScheduleChange)):
                if self.now_decimal >= self.newTimeScheduleChange[index]:
                    _pastSchedule.append(self.newTimeScheduleChange[index])

            # if length of _pastSchedule is not 0, there is a previous schedule(s)
            if len(_pastSchedule) != 0:
                # previous schedule exists, use previous schedule to update thermostat to latest setting
                _latest_schedule = max(_pastSchedule)
                self.current_use_schedule = _latest_schedule
                _time_current_schedule = int(self.current_use_schedule)
                self.hour_current_schedule = int(_time_current_schedule/60)
                self.minute_current_schedule = int(_time_current_schedule - self.hour_current_schedule*60)
                self.status_brightness_color_current = str(self.timeStatusBrightnessColor[str(self.current_use_schedule)]).split('|')
                self.statusToChange_current = self.status_brightness_color_current[0]
                self.brightnessToChange_current = self.status_brightness_color_current[1]
                self.colorToChange_current = self.status_brightness_color_current[2]
                self.flag_time_to_change_status = True
                print "{} for Agent: {} >> Here is the new schedule: at {} hr {} min status: {}, " \
                      "brightness: {}, color: {}".format(app_name, agent_id, self.hour_current_schedule,
                                                         self.minute_current_schedule, str(self.statusToChange_current)
                                                         .upper(), str(self.brightnessToChange_current),
                                                         str(self.colorToChange_current))

            else:  # previous schedule does not exist
                # scheduler is trying to get setting from the old setting file
                if self.current_use_schedule is not None:  # previous schedule from old setting file exists
                    _time_current_schedule = int(self.current_use_schedule)
                    self.hour_current_schedule = int(_time_current_schedule/60)
                    self.minute_current_schedule = int(_time_current_schedule - self.hour_current_schedule*60)
                    self.status_brightness_color_current = str(self.timeStatusBrightnessColor[str(self.current_use_schedule)]).split('|')
                    self.statusToChange_current = self.status_brightness_color_current[0]
                    self.brightnessToChange_current = self.status_brightness_color_current[1]
                    self.colorToChange_current = self.status_brightness_color_current[2]
                    self.flag_time_to_change_status = True

                    print "{} for Agent: {} >> previous schedule is at {} hr {} min status: {}, brightness: {}," \
                          " color: {}".format(app_name, agent_id, str(self.hour_current_schedule),
                                              str(self.minute_current_schedule), str(self.statusToChange_current).upper()
                                              , str(self.brightnessToChange_current, str(self.colorToChange_current)))

                else:  # previous schedule from old setting file does not exist
                    print "{} for Agent: {} >> There is no previous schedule from old setting file".format(app_name,
                                                                                                           agent_id)
                    print '{} for Agent: {} >> Let''s check for the next schedule'.format(app_name, agent_id)

            # 2.  take action based on current time
            # 2.1 case 1: time to change schedule is triggered
            if self.flag_time_to_change_status is True:
                if debug_agent: print "{} for Agent: {} >> is changing the lighting status, brightness, and color"\
                    .format(app_name, agent_id)
                try:
                    _headers = {
                        headers_mod.FROM: agent_id,
                        headers_mod.CONTENT_TYPE: headers_mod.CONTENT_TYPE.JSON,
                    }
                    # case1: only 'status' is changed
                    if str(self.brightnessToChange_current) == "None" and str(self.colorToChange_current) == "None":
                        if str(self.statusToChange_current) != "None": #send only status
                            _status_to_publish = str(self.statusToChange_current).upper()
                            _content = {"status": _status_to_publish}
                            print "{} for Agent: {} >> published message to IEB with status: {}"\
                                .format(app_name, agent_id, _status_to_publish)
                            self.publish(topic_app_agent, _headers, json.dumps(_content))
                        else: # nothing to publish
                            pass
                    # case2: 'status' with 'brightness' or 'color' are changed
                    elif str(self.brightnessToChange_current) == "None" or str(self.colorToChange_current) == "None":
                        if str(self.statusToChange_current) != "None" and str(self.brightnessToChange_current) != "None":
                            _status_to_publish = str(self.statusToChange_current).upper()
                            _brightness_to_publish = int(self.brightnessToChange_current)
                            _content = {"status": _status_to_publish, "brightness": _brightness_to_publish}
                            print "{} for Agent: {} >> published message to IEB with status: {}, brightness: {}"\
                                .format(app_name, agent_id, _status_to_publish, _brightness_to_publish)
                            self.publish(topic_app_agent, _headers, json.dumps(_content))
                        elif str(self.statusToChange_current) != "None" and str(self.colorToChange_current) != "None":
                            _status_to_publish = str(self.statusToChange_current).upper()
                            _color_temp1 = str(self.colorToChange_current)
                            _color_temp2 = tuple(int(v) for v in re.findall("[0-9]+", _color_temp1))
                            _color_to_publish = _color_temp2
                            _content = {"status": _status_to_publish, "color": _color_to_publish}
                            print "{} for Agent: {} >> published message to IEB with status: {}, color: {}"\
                                .format(app_name, agent_id, _status_to_publish, _color_to_publish)
                            self.publish(topic_app_agent, _headers, json.dumps(_content))
                        else:  # nothing to publish
                            pass
                    # case3: 'status' with 'brightness' with 'color' are changed
                    else:
                        _status_to_publish = str(self.statusToChange_current).upper()
                        _brightness_to_publish = int(self.brightnessToChange_current)
                        _color_temp1 = str(self.colorToChange_current)
                        _color_temp2 = tuple(int(v) for v in re.findall("[0-9]+", _color_temp1))
                        _color_to_publish = _color_temp2
                        _content = {"status": _status_to_publish, "color": _color_to_publish, "brightness": _brightness_to_publish}
                        print "{} for Agent: {} >> published message to IEB with status: {}, brightness: {}, color: {}"\
                            .format(app_name, agent_id, _status_to_publish, _brightness_to_publish, _color_to_publish)
                        self.publish(topic_app_agent, _headers, json.dumps(_content))

                    self.flag_time_to_change_status = False
                except:
                    print "{} for Agent: {} >> ERROR changing status of a light"\
                        .format(app_name, agent_id)
            # 2.2 case2: time to change schedule is not triggered
            else:
                pass
                # print("Scheduler Agent takes no action")

            # 3. check next schedule
            # 3.1 check whether there is a next schedule
            _nextSchedule = list()
            for index in range(len(self.newTimeScheduleChange)):
                if self.now_decimal < self.newTimeScheduleChange[index]:
                    _nextSchedule.append(self.newTimeScheduleChange[index])

            if len(_nextSchedule) != 0:
                _time_next_schedule = int(min(_nextSchedule))
                self.hour_next_schedule = int(_time_next_schedule/60)
                self.minute_next_schedule = int(_time_next_schedule - (self.hour_next_schedule*60))
                self.status_brightness_color_next = str(self.timeStatusBrightnessColor[str(min(_nextSchedule))]).split('|')
                self.statusToChange_next = self.status_brightness_color_next[0]
                self.brightnessToChange_next = self.status_brightness_color_next[1]
                self.colorToChange_next = self.status_brightness_color_next[2]
                print "{} for Agent: {} >> Here is the next schedule: at {} hr {} min status: {}, brightness: {}, color: {}".\
                        format(app_name, agent_id, self.hour_next_schedule, self.minute_next_schedule, 
                               str(self.statusToChange_next).upper(), self.brightnessToChange_next, self.colorToChange_next)
                self.time_next_schedule_sec = int(_time_next_schedule*60)
                _time_to_wait = self.time_next_schedule_sec - self.time_now_sec
                if _time_to_wait >= 3600:
                    _hr_to_wait = int(_time_to_wait/3600)
                    _min_to_wait = int((_time_to_wait - (_hr_to_wait*3600))/60)
                    _sec_to_wait = int(_time_to_wait - (_hr_to_wait*3600) - (_min_to_wait*60))
                elif _time_to_wait > 60:
                    _hr_to_wait = 0
                    _min_to_wait = int(_time_to_wait/60)
                    _sec_to_wait = int(_time_to_wait - (_min_to_wait*60))
                else:
                    _hr_to_wait = 0
                    _min_to_wait = 0
                    _sec_to_wait = _time_to_wait
                print "{} for Agent: {} >> is going to sleep now until next schedule come up in {} hr {} min {} sec"\
                    .format(app_name, agent_id, _hr_to_wait, _min_to_wait, _sec_to_wait)
            else:
                print "{} for Agent: {} >> There is no next schedule".format(app_name, agent_id)
                self.time_next_schedule_sec = int(24*3600)
            print '---------------------------------'

        def find_day(self):
            localtime = time.localtime(time.time())
            today = None
            if localtime.tm_wday == 0:
                today = 'monday'
            elif localtime.tm_wday == 1:
                today = 'tuesday'
            elif localtime.tm_wday == 2:
                today = 'wednesday'
            elif localtime.tm_wday == 3:
                today = 'thursday'
            elif localtime.tm_wday == 4:
                today = 'friday'
            elif localtime.tm_wday == 5:
                today = 'saturday'
            elif localtime.tm_wday == 6:
                today = 'sunday'
            return today

        def set_variable(self, k, v):  # k=key, v=value
            self.variables[k] = v

        def get_variable(self, k):
            return self.variables.get(k, None)  # default of get_variable is none

    Agent.__name__ = 'Lighting Scheduler Agent'
    return Agent(**kwargs)

def main(argv=sys.argv):
    '''Main method called by the eggsecutable.'''
    utils.default_main(scheduleragent,
                       description='Lighting Scheduler Agent',
                       argv=argv)

if __name__ == '__main__':
    # Entry point for script
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        pass
