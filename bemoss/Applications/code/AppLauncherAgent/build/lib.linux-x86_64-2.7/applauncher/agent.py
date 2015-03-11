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
__created__ = "2014-8-28 16:19:00"
__lastUpdated__ = "2015-02-11 17:12:03"
'''

import logging
import sys
import datetime
import json
import os
from volttron.lite.agent import BaseAgent, PublishMixin, periodic
from volttron.lite.agent import utils, matching
from volttron.lite.messaging import headers as headers_mod
import settings
import psycopg2  # PostgresQL database adapter
import re

utils.setup_logging()
_log = logging.getLogger(__name__)
app_name = "appLauncher"
debug_agent = False
clock_time = 1
time_to_start_previous_apps = 30  # sec

#@params agent & DB interfaces
db_host = settings.DATABASES['default']['HOST']
db_port = settings.DATABASES['default']['PORT']
db_database = settings.DATABASES['default']['NAME']
db_user = settings.DATABASES['default']['USER']
db_password = settings.DATABASES['default']['PASSWORD']
db_table_application_registered = settings.DATABASES['default']['TABLE_application_registered']
db_table_application_running = settings.DATABASES['default']['TABLE_application_running']

class AppLauncherAgent(PublishMixin, BaseAgent):
    '''Listens to UI to launch new APP in the BEMOSS APP Store'''
    def __init__(self, config_path, **kwargs):
        super(AppLauncherAgent, self).__init__(**kwargs)
        self.config = utils.load_config(config_path)
        # self.app_number = 0
        #connect to the database
        try:
            self.con = psycopg2.connect(host=db_host, port=db_port, database=db_database, user=db_user,
                                        password=db_password)
            self.cur = self.con.cursor()  # open a cursor to perform database operations
            print("AppLauncher Agent connects to the database name {} successfully".format(db_database))
        except:
            print("ERROR: {} fails to connect to the database name {}".format(app_name, db_database))

        self.time_applauncher_start = datetime.datetime.now()
        self.already_started_previous_apps = False

    def setup(self):
        # Demonstrate accessing a value from the config file
        _log.info(self.config['message'])
        self._agent_id = self.config['agentid']
        # Always call the base class setup()
        super(AppLauncherAgent, self).setup()
        # self.appLauncherInitiator()
        print "AppLauncher Agent is waiting for UI to activate/disable APPs"

    # clockBehavior (CyclicBehavior)
    @periodic(clock_time)
    def clockBehavior(self):
        #1. check current time
        self.time_applauncher_now = datetime.datetime.now()
        if self.already_started_previous_apps:
            # print "AppLauncher Agent >> appLauncherInitiator has already run"
            pass
        else:
            # print "AppLauncher Agent >> appLauncherInitiator has not run yet"
            if (self.time_applauncher_now - self.time_applauncher_start).seconds > time_to_start_previous_apps:
                print "AppLauncher Agent is starting previously running Apps"
                self.appLauncherInitiator()
                self.already_started_previous_apps = True
            else:
                pass

    # Add Cyclic behavior to track current status of app then update DB
    def appLauncherInitiator(self):
        try:
            self.cur.execute("SELECT * FROM "+db_table_application_running)
            # self.cur.execute("SELECT status FROM applications_running WHERE app_name=%s", (ui_app_name,))
            print self.cur.rowcount
            if self.cur.rowcount != 0:
                all_row = self.cur.fetchall()
                for row in all_row:
                    if row[3] == 'running':  # rerun app for the agent
                        # To launch agent: 1.get app_name, 2.get agent_id, 3.get auth_token
                        print "This {} is {}".format(row[1], row[3])
                        _temp_app_agent_id = str(row[1]).split('_')
                        app_name = _temp_app_agent_id[0]+'_'+_temp_app_agent_id[1]
                        agent_id = _temp_app_agent_id[2]
                        self.cur.execute("SELECT auth_token FROM "+db_table_application_registered+" WHERE app_name=%s",
                                         (app_name,))
                        if self.cur.rowcount != 0:
                            auth_token = str(self.cur.fetchone()[0])
                        app_setting = row[4]
                        print "AppLauncher >> is trying the previous run App {} for agent {} with auth_token {} and " \
                              "app_setting {}".format(app_name, agent_id, auth_token, app_setting)
                        self.app_has_already_launched = False
                        self.launch_app(app_name, agent_id, auth_token)
                    else:  # do nothing
                        print "This {} is {}".format(row[1], row[3])
            else:
                print "AppLauncher >> no App was running"
        except:
            "AppLauncher >> failed to launch the previous run Apps"

    # on_match (Cyclic Behavior) to filter message from the UI to launch new APP
    @matching.match_start('/ui/appLauncher/')
    def on_match(self, topic, headers, message, match):
        print "AppLauncher Agent got Topic: {topic}".format(topic=topic)
        _sub_topic = str(topic).split('/')
        app_name = _sub_topic[3]
        agent_id = _sub_topic[4]
        _data = json.dumps(message[0])
        _data = json.loads(message[0])
        auth_token = _data.get('auth_token')
        if _sub_topic[5] == 'launch':
            self.app_has_already_launched = False
            self.launch_app(app_name, agent_id, auth_token)
        elif _sub_topic[5] == 'disable':
            self.app_has_already_launched = False
            self.disable_app(app_name, agent_id, auth_token)
        else:
            "AppLauncher Agent does not understand this message"

    def launch_app(self, ui_app_name, ui_agent_id, ui_auth_token):
        #1. query database whether the app_name is verified and registered
        #if app_name is in database with the valid authorization_token, then launch agent
        self.cur.execute("SELECT auth_token FROM "+db_table_application_registered+" WHERE app_name=%s", (ui_app_name,))
        if self.cur.rowcount != 0:
            app_auth_token = self.cur.fetchone()[0]
            if ui_auth_token == app_auth_token:
                # 1. launch app
                PROJECT_DIR = settings.PROJECT_DIR
                sys.path.append(PROJECT_DIR)
                os.system("bin/volttron-ctrl list-agent > app_running_agent.txt")
                infile = open('app_running_agent.txt', 'r')
                for line in infile:
                    #print(line, end='') #write to a next file name outfile
                    match = re.search(ui_app_name+'_'+ui_agent_id+'.launch.json', line) \
                            and re.search('running', line)  # have results in match
                    if match: # The app that ui requested has already launched
                        self.app_has_already_launched = True
                        print "AppLauncher failed to launch APP: {}, APP has actually been launched"\
                            .format(ui_app_name)
                        print "AppLauncher >> {}".format(line)

                if self.app_has_already_launched:
                    _launch_file_to_check = str(ui_app_name) + "_" + str(ui_agent_id)
                    self.cur.execute("SELECT status FROM "+db_table_application_running+" WHERE app_agent_id=%s",
                                     (_launch_file_to_check,))
                    if self.cur.rowcount != 0:  # this APP used to be launched before
                        _app_status = str(self.cur.fetchone()[0])
                        if _app_status == "running": # no need to launch new app
                            pass
                        else:
                            self.cur.execute("UPDATE application_running SET status=%s WHERE app_agent_id=%s",
                                     ("running", _launch_file_to_check,))
                            self.con.commit()
                    else:
                        # 2. log app that has been launched to the database
                        _launch_file_name = str(ui_app_name) + "_" + str(ui_agent_id)
                        _start_time = str(datetime.datetime.now())
                        _app_status = "running"
                        self.cur.execute("SELECT application_id FROM "+db_table_application_running)
                        if self.cur.rowcount != 0:
                            # print 'cur.fetchall()' + str(max(cur.fetchall())[0])
                            app_no = max(self.cur.fetchall())[0] + 1
                        else: #default no_app
                            app_no = 1
                        self.cur.execute("INSERT INTO application_running(application_id, app_agent_id, start_time, status) "
                             "VALUES(%s,%s,%s,%s)",
                             (app_no, _launch_file_name, _start_time, _app_status))
                        self.con.commit()
                        print "AppLauncher >> the requested APP {} for {} is running but not in db, " \
                              "now it is added to db".format(ui_app_name, ui_agent_id)
                        print "AppLauncher >> NOTE Date and Time launch APP is the current time not actual time"

                    _topic_appLauncher_ui = '/appLauncher/ui/' + ui_app_name + '/' + ui_agent_id + '/' \
                                            + 'launch/response'
                    _headers = {
                        headers_mod.FROM: app_name,
                        headers_mod.CONTENT_TYPE: headers_mod.CONTENT_TYPE.JSON,
                    }
                    _message = "failure"
                    self.publish(_topic_appLauncher_ui, _headers, _message)
                else: # APP has not launched yet
                    _launch_file_to_check = str(ui_app_name) + "_" + str(ui_agent_id)
                    self.cur.execute("SELECT status FROM "+db_table_application_running+" WHERE app_agent_id=%s",
                                     (_launch_file_to_check,))
                    if self.cur.rowcount != 0: # delete existing row from the table before launching new app
                        # self.cur.execute("DELETE FROM "+db_table_application_running+" WHERE app_agent_id=%s",
                        #                  (_launch_file_to_check,))
                        # self.con.commit()
                        self.launch_existing_app(ui_app_name, ui_agent_id)
                    else: #this APP has never been launched and not in db launch new app
                        self.launch_new_app(ui_app_name, ui_agent_id)
            else:
                print "UI failed to authorize with AppLauncher Agent before launching the requested APP"
        else:
            print "The APP that UI requested is neither REGISTERED nor AVAILABLE"

    def launch_existing_app(self, ui_app_name, ui_agent_id):
        self.cur.execute("SELECT executable FROM "+db_table_application_registered+" WHERE app_name=%s", (ui_app_name,))
        # 1. launch app for an agent based on the exec file and agent_id
        if self.cur.rowcount != 0:
            _exec_name = str(self.cur.fetchone()[0])
            _exec = _exec_name+"-0.1-py2.7.egg --config \"%c\" --sub \"%s\" --pub \"%p\""
            data = {
                "agent": {
                    "exec": _exec
                },
                "agent_id": ui_agent_id
            }
            PROJECT_DIR = settings.PROJECT_DIR
            _launch_file = os.path.join(PROJECT_DIR, "bemoss/Applications/launch/"
                                        + str(ui_app_name) + "_" + str(ui_agent_id) +".launch.json")
            if debug_agent: print(_launch_file)
            with open(_launch_file, 'w') as outfile:
                json.dump(data, outfile, indent=4, sort_keys=True)
            if debug_agent: print(os.path.basename(_launch_file))
            os.system("bin/volttron-ctrl load-agent "+_launch_file)
            os.system("bin/volttron-ctrl start-agent "+os.path.basename(_launch_file))
            os.system("bin/volttron-ctrl list-agent")
            print "AppLauncher has successfully launched APP: {} for Agent: {}"\
                .format(ui_app_name, ui_agent_id)
            # send reply back to UI
            _topic_appLauncher_ui = '/appLauncher/ui/' + ui_app_name + '/' + ui_agent_id + '/' + 'launch/response'
            _headers = {
                headers_mod.FROM: app_name,
                headers_mod.CONTENT_TYPE: headers_mod.CONTENT_TYPE.JSON,
            }
            _message = "success"
            self.publish(_topic_appLauncher_ui, _headers, _message)

    def launch_new_app(self, ui_app_name, ui_agent_id):
        self.cur.execute("SELECT executable FROM "+db_table_application_registered+" WHERE app_name=%s", (ui_app_name,))
        # 1. launch app for an agent based on the exec file and agent_id
        if self.cur.rowcount != 0:
            _exec_name = str(self.cur.fetchone()[0])
            _exec = _exec_name+"-0.1-py2.7.egg --config \"%c\" --sub \"%s\" --pub \"%p\""
            data = {
                "agent": {
                    "exec": _exec
                },
                "agent_id": ui_agent_id
            }
            PROJECT_DIR = settings.PROJECT_DIR
            _launch_file = os.path.join(PROJECT_DIR, "bemoss/Applications/launch/"
                                        + str(ui_app_name) + "_" + str(ui_agent_id) +".launch.json")
            if debug_agent: print(_launch_file)
            with open(_launch_file, 'w') as outfile:
                json.dump(data, outfile, indent=4, sort_keys=True)
            if debug_agent: print(os.path.basename(_launch_file))
            os.system("bin/volttron-ctrl load-agent "+_launch_file)
            os.system("bin/volttron-ctrl start-agent "+os.path.basename(_launch_file))
            os.system("bin/volttron-ctrl list-agent")
            print "AppLauncher has successfully launched APP: {} for Agent: {}"\
                .format(ui_app_name, ui_agent_id)
            # send reply back to UI
            _topic_appLauncher_ui = '/appLauncher/ui/' + ui_app_name + '/' + ui_agent_id + '/' + 'launch/response'
            _headers = {
                headers_mod.FROM: app_name,
                headers_mod.CONTENT_TYPE: headers_mod.CONTENT_TYPE.JSON,
            }
            _message = "success"
            self.publish(_topic_appLauncher_ui, _headers, _message)
            # self.app_number += 1
            self.cur.execute("SELECT description FROM "+db_table_application_registered+" WHERE app_name=%s", (ui_app_name,))
            if self.cur.rowcount != 0:
                _app_description = str(self.cur.fetchone()[0])
                print "The description of APP: {} is {}".format(ui_app_name, _app_description)
            else:
                print "AppLauncher failed to get APP: {} description".format(ui_app_name)

            # 2. log app that has been launched to the database
            _launch_file_name = str(ui_app_name) + "_" + str(ui_agent_id)
            _start_time = str(datetime.datetime.now())
            _app_status = "running"
            self.cur.execute("SELECT application_id FROM "+db_table_application_running)
            if self.cur.rowcount != 0:
                # print 'cur.fetchall()' + str(max(cur.fetchall())[0])
                app_no = max(self.cur.fetchall())[0] + 1
            else: #default no_app
                app_no = 1
            self.cur.execute("INSERT INTO application_running(application_id, app_agent_id, start_time, status) "
                             "VALUES(%s,%s,%s,%s)",
                             (app_no, _launch_file_name, _start_time, _app_status))
            self.con.commit()
            print "AppLauncher finished update table applications_running of APP: {}".format(ui_app_name)
            print "with launch_file: {}, at timestamp {}".format(_launch_file, _start_time)
        else:
            print "AppLauncher failed to launch APP: {} for Agent: {}".format(ui_app_name, ui_agent_id)

    def disable_app(self, ui_app_name, ui_agent_id, ui_auth_token):
        #1. query database whether the ui_app_name is verified and registered
        self.cur.execute("SELECT auth_token FROM "+db_table_application_registered+" WHERE app_name=%s", (ui_app_name,))
        if self.cur.rowcount != 0:
            app_auth_token = self.cur.fetchone()[0]
            if ui_auth_token == app_auth_token:
                #check whether the ui_app_name and ui_agent_id is actually running
                PROJECT_DIR = settings.PROJECT_DIR
                sys.path.append(PROJECT_DIR)
                os.system("bin/volttron-ctrl list-agent > app_running_agent.txt")
                infile = open('app_running_agent.txt', 'r')
                for line in infile:
                    #print(line, end='') #write to a next file name outfile
                    match = re.search(ui_app_name+'_'+ui_agent_id+'.launch.json', line) \
                            and re.search('running', line)  # have results in match
                    if match: # The app that ui requested has already launched
                        self.app_has_already_launched = True
                    else:
                        pass

                if self.app_has_already_launched:
                    _launch_file_to_check = str(ui_app_name) + "_" + str(ui_agent_id)
                    self.cur.execute("SELECT status FROM "+db_table_application_running+" WHERE app_agent_id=%s",
                                     (_launch_file_to_check,))
                    if self.cur.rowcount != 0:
                        _app_status = str(self.cur.fetchone()[0])
                        #if it's running disable app
                        if _app_status == "running":
                            _lauch_file_to_disable = _launch_file_to_check+".launch.json"
                            os.system("bin/volttron-ctrl stop-agent "+_lauch_file_to_disable)
                            os.system("bin/volttron-ctrl list-agent")
                            print "AppLauncher has successfully disabled APP: {} ".format(ui_app_name)
                            self.cur.execute("UPDATE application_running SET status=%s WHERE app_agent_id=%s"
                                             , ('disabled', _launch_file_to_check))
                            self.con.commit()
                            # send reply back to UI
                            topic_appLauncher_ui = '/appLauncher/ui/' + ui_app_name + '/' + ui_agent_id + '/' \
                                                   + 'disable/response'
                            headers = {
                                headers_mod.FROM: app_name,
                                headers_mod.CONTENT_TYPE: headers_mod.CONTENT_TYPE.JSON,
                            }
                            message = "success"
                            self.publish(topic_appLauncher_ui, headers, message)
                        elif _app_status == "disabled":
                            print "AppLauncher: the requested APP: {} for Agent: {} has already disabled"\
                                .format(ui_app_name, ui_agent_id)
                        else:
                            print "AppLauncher: the requested APP: {} for Agent: {} has unknown status"\
                                .format(ui_app_name, ui_agent_id)
                    else:
                        print "AppLauncher: APP {} for Agent: {} is not running".format(ui_app_name, ui_agent_id)
                else: # app is acutally not running no need to do action
                    "AppLauncher: discard request to disable APP: {} for Agent: {} since it's not running"\
                        .format(ui_app_name, ui_agent_id)
            else:
                print "UI failed to authorize with AppLauncher Agent before disabling the requested APP"
        else:
            print "The APP that UI requested is neither REGISTERED nor AVAILABLE"

def main(argv=sys.argv):
    '''Main method called by the eggsecutable.'''
    try:
        utils.default_main(AppLauncherAgent,
                           description='this is an AppLauncher agent',
                           argv=argv)
    except Exception as e:
        _log.exception('unhandled exception')

if __name__ == '__main__':
    # Entry point for script
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        pass
