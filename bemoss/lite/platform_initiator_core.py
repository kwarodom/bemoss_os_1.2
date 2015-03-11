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
__maintainer__ = "Warodom Khamphanchai"
__email__ = "kwarodom@vt.edu"
__website__ = "kwarodom.wordpress.com"
__status__ = "Prototype"
__created__ = "2014-8-29 17:15:00"
__lastUpdated__ = "2015-02-11 21:47:26"
'''

import os
import sys
os.chdir(os.path.expanduser("~/workspace/bemoss_os/"))  # = ~/workspace/bemoss_os
current_working_directory = os.getcwd()
sys.path.append(current_working_directory)
import settings
import psycopg2
import datetime

# CONFIGURATION ---------------------------------------------------------------------------------------------
# @params agent
agent_id = 'PlatformInitiator'

# @params DB interfaces
db_database = settings.DATABASES['default']['NAME']
db_host = settings.DATABASES['default']['HOST']
db_port = settings.DATABASES['default']['PORT']
db_user = settings.DATABASES['default']['USER']
db_password = settings.DATABASES['default']['PASSWORD']
db_table_building_zone = settings.DATABASES['default']['TABLE_building_zone']
db_table_global_zone_setting = settings.DATABASES['default']['TABLE_global_zone_setting']
db_table_holiday = settings.DATABASES['default']['TABLE_holiday']
db_table_applications_running = settings.DATABASES['default']['TABLE_application_running']
db_table_device_info = settings.DATABASES['default']['TABLE_device_info']
db_table_application_running = settings.DATABASES['default']['TABLE_application_running']
db_table_application_registered = settings.DATABASES['default']['TABLE_application_registered']
db_table_plugload = settings.DATABASES['default']['TABLE_plugload']
db_table_thermostat = settings.DATABASES['default']['TABLE_thermostat']
db_table_lighting = settings.DATABASES['default']['TABLE_lighting']
db_table_device_metadata = settings.DATABASES['default']['TABLE_device_metadata']
# @paths
PROJECT_DIR = settings.PROJECT_DIR
Agents_Launch_DIR = settings.Agents_Launch_DIR
Loaded_Agents_DIR = settings.Loaded_Agents_DIR
Autostart_Agents_DIR = settings.Autostart_Agents_DIR
Applications_Launch_DIR = settings.Applications_Launch_DIR
# ----------------------------------------------------------------------------------------------------------
os.system("clear")
# 1. Connect to bemossdb database
conn = psycopg2.connect(host=db_host, port=db_port, database=db_database,
                            user=db_user, password=db_password)
cur = conn.cursor()  # open a cursor to perform database operations
print "{} >> Done 1: connect to database name {}".format(agent_id, db_database)

# 2. clean all tables
# cur.execute("DELETE FROM "+db_table_application_registered)
# conn.commit()
cur.execute("DELETE FROM "+db_table_thermostat)
conn.commit()
cur.execute("DELETE FROM "+db_table_lighting)
conn.commit()
cur.execute("DELETE FROM "+db_table_plugload)
conn.commit()
cur.execute("DELETE FROM "+db_table_device_info)
conn.commit()
cur.execute("DELETE FROM "+db_table_global_zone_setting)
conn.commit()
cur.execute("DELETE FROM "+db_table_building_zone)
conn.commit()
# cur.execute("DELETE FROM "+db_table_building_zone+" WHERE zone_id=999")
# conn.commit()
cur.execute("select * from information_schema.tables where table_name=%s", ('holiday',))
print bool(cur.rowcount)
if bool(cur.rowcount):
    cur.execute("DELETE FROM "+db_table_holiday)
    conn.commit()
else:
    pass
cur.execute("select * from information_schema.tables where table_name=%s", (db_table_applications_running,))
if bool(cur.rowcount):
    cur.execute("DELETE FROM "+db_table_applications_running)
    conn.commit()
print "{} >> Done 2: clear all tables".format(agent_id)

# 3. add holidays ref www.archieves.gov/news/federal-holidays.html
cur.execute("INSERT INTO "+db_table_holiday+" VALUES(%s,%s,%s)",
            (1, datetime.datetime(2014, 01, 01).date(), "New Year's Day"))
cur.execute("INSERT INTO "+db_table_holiday+" VALUES(%s,%s,%s)",
            (2, datetime.datetime(2014, 1, 20).date(), "Birthday of Martin Luther King Jr."))
cur.execute("INSERT INTO "+db_table_holiday+" VALUES(%s,%s,%s)",
            (3, datetime.datetime(2014, 2, 17).date(), "Washington's Birthday"))
cur.execute("INSERT INTO "+db_table_holiday+" VALUES(%s,%s,%s)",
            (4, datetime.datetime(2014, 5, 26).date(), "Memorial Day"))
cur.execute("INSERT INTO "+db_table_holiday+" VALUES(%s,%s,%s)",
            (5, datetime.datetime(2014, 7, 4).date(), "Independence Day"))
cur.execute("INSERT INTO "+db_table_holiday+" VALUES(%s,%s,%s)",
            (6, datetime.datetime(2014, 9, 1).date(), "Labor Day"))
cur.execute("INSERT INTO "+db_table_holiday+" VALUES(%s,%s,%s)",
            (7, datetime.datetime(2014, 10, 13).date(), "Columbus Day"))
cur.execute("INSERT INTO "+db_table_holiday+" VALUES(%s,%s,%s)",
            (8, datetime.datetime(2014, 11, 11).date(), "Veterans Day"))
cur.execute("INSERT INTO "+db_table_holiday+" VALUES(%s,%s,%s)",
            (9, datetime.datetime(2014, 11, 27).date(), "Thanksgiving Day"))
cur.execute("INSERT INTO "+db_table_holiday+" VALUES(%s,%s,%s)",
            (10, datetime.datetime(2014, 12, 25).date(), "Christmas Day"))
conn.commit()
print "{} >> Done 3: added holidays to {}".format(agent_id, db_table_holiday)

# 4. clear all previous agent launch files
loaded_agents = os.listdir(Loaded_Agents_DIR)
if len(loaded_agents) != 0:
    os.system("rm "+Loaded_Agents_DIR+"*")
    print "{} >> Done 4: agent launch files are removed from {}".format(agent_id, Loaded_Agents_DIR)
else:
    pass

# 5. clear all previous agent autostart files
auto_start_agents = os.listdir(Autostart_Agents_DIR)
if len(auto_start_agents) != 0:
    os.system("rm "+Autostart_Agents_DIR+"*")
    print "{} >> Done 5: agent autostart files are removed from {}".format(agent_id, Autostart_Agents_DIR)
else:
    pass

# 6. clear all previous agent launch files
agent_launch_files = os.listdir(Agents_Launch_DIR)
if len(agent_launch_files) != 0:
    os.system("rm "+Agents_Launch_DIR+"*")
    print "{} >> Done 6: agent launch files are removed from {}".format(agent_id, Agents_Launch_DIR)
else:
    pass

# 7. check and confirm zone id:999 (unassigned for newly discovered devices) is in table
cur.execute("SELECT zone_id FROM "+db_table_building_zone+" WHERE zone_id=999")
if cur.rowcount == 0:
    cur.execute("INSERT INTO "+db_table_building_zone+" VALUES(%s, %s)", (999, "BEMOSS Core"))
    conn.commit()
    print "{} >> Done 7: default columns zone_id 999 and zone_nickname BEMOSS Core " \
          "is inserted into {} successfully".format(agent_id, db_table_building_zone)
else:
    print "{} >> Warning: default zone 999 already exists".format(agent_id)

# 8. check and confirm zone id:999 (BEMOSS Core for newly discovered devices) is in table
cur.execute("SELECT id FROM "+db_table_global_zone_setting+" WHERE zone_id=%s", (999,))
if cur.rowcount == 0:  # this APP used to be launched before
    cur.execute("INSERT INTO "+db_table_global_zone_setting+"(id, zone_id, heat_setpoint, cool_setpoint, illuminance)"
                                                            " VALUES(%s,%s,%s,%s,%s)", (999,999,70,78,80,))
    conn.commit()
else:
    print "{} >> Warning: default zone 999 already exists".format(agent_id)

# 9. create tables
cur.execute("select * from information_schema.tables where table_name=%s", ('application_running',))
print bool(cur.rowcount)
if bool(cur.rowcount):
    cur.execute("DROP TABLE application_running")
    conn.commit()
else:
    pass

cur.execute('''CREATE TABLE application_running
       (APPLICATION_ID SERIAL   PRIMARY KEY   NOT NULL,
       APP_AGENT_ID   VARCHAR(50)   NOT NULL,
       START_TIME     TIMESTAMP,
       STATUS        VARCHAR(10),
       APP_SETTING   VARCHAR(200));''')
print "Table application_running created successfully"
conn.commit()

cur.execute("select * from information_schema.tables where table_name=%s", ('application_registered',))
print bool(cur.rowcount)
if bool(cur.rowcount):
    cur.execute("DROP TABLE application_registered")
    conn.commit()
else:
    pass

cur.execute('''CREATE TABLE application_registered
       (APPLICATION_ID SERIAL   PRIMARY KEY   NOT NULL,
       APP_NAME VARCHAR (30) NOT NULL,
       EXECUTABLE VARCHAR (35) NOT NULL,
       AUTH_TOKEN VARCHAR (20) NOT NULL,
       APP_USER TEXT,
       DESCRIPTION  VARCHAR (200) NOT NULL,
       REGISTERED_TIME  TIMESTAMP  NOT NULL,
       LAST_UPDATED_TIME  TIMESTAMP NOT NULL);''')
print "Table application_registered created successfully"
conn.commit()

# cur.execute("select * from information_schema.tables where table_name=%s", ('device_info',))
# print bool(cur.rowcount)
# if bool(cur.rowcount):
#     cur.execute("DROP TABLE device_info")
#     conn.commit()
# else:
#     pass
#
# cur.execute('''CREATE TABLE device_info
#        (DEVICE_ID VARCHAR(50) PRIMARY KEY   NOT NULL,
#        DEVICE_TYPE   VARCHAR(20)   NOT NULL,
#        VENDOR_NAME  VARCHAR(50) NOT NULL,
#        DEVICE_MODEL VARCHAR(30) NOT NULL,
#        DEVICE_MODEL_ID VARCHAR(5) NOT NULL,
#        MAC_ADDRESS  MACADDR NOT NULL,
#        MIN_RANGE  INT,
#        MAX_RANGE INT,
#        IDENTIFIABLE BOOLEAN NOT NULL,
#        COMMUNICATION VARCHAR(10) NOT NULL,
#        DATE_ADDED     TIMESTAMP,
#        FACTORY_ID     VARCHAR(50));''')
# print "Table device_info created successfully"
# conn.commit()

# cur.execute("select * from information_schema.tables where table_name=%s", ('plugload',))
# print bool(cur.rowcount)
# if bool(cur.rowcount):
#     cur.execute("DROP TABLE plugload")
#     conn.commit()
# else:
#     pass
#
# cur.execute('''CREATE TABLE plugload
#        (PLUGLOAD_ID VARCHAR(50) PRIMARY KEY   NOT NULL,
#        STATUS   VARCHAR(3),
#        POWER    FLOAT,
#        ENERGY   FLOAT,
#        IP_ADDRESS INET,
#        NICKNAME VARCHAR(30) NOT NULL,
#        ZONE_ID INT NOT NULL,
#        NETWORK_STATUS VARCHAR(7) NOT NULL,
#        OTHER_PARAMETERS VARCHAR(200),
#        LAST_SCANNED_TIME TIMESTAMP,
#        LAST_OFFLINE_TIME TIMESTAMP);''')
# print "Table plugload created successfully"
# conn.commit()

# cur.execute("select * from information_schema.tables where table_name=%s", ('device_api',))
# print bool(cur.rowcount)
# if bool(cur.rowcount):
#     cur.execute("DROP TABLE device_api")
#     conn.commit()
# else:
#     pass
#
# cur.execute('''CREATE TABLE device_api
#        (DEVICE_API_ID SERIAL   PRIMARY KEY   NOT NULL,
#        DEVICE_MODEL_ID VARCHAR(5) NOT NULL,
#        API_INTERFACE VARCHAR(20) NOT NULL,
#        DATE_ADDED DATE NOT NULL,
#        LATE_UPDATED DATE NOT NULL);''')
# print "Table device_api created successfully"
# conn.commit()

# cur.execute("select * from information_schema.tables where table_name=%s", ('thermostat',))
# print bool(cur.rowcount)
# if bool(cur.rowcount):
#     cur.execute("DROP TABLE thermostat")
#     conn.commit()
# else:
#     pass
#
# cur.execute('''CREATE TABLE thermostat
#        (THERMOSTAT_ID VARCHAR(50) PRIMARY KEY   NOT NULL,
#        TEMPERATURE   FLOAT,
#        THERMOSTAT_MODE   VARCHAR(4),
#        FAN_MODE VARCHAR(10),
#        HEAT_SETPOINT  FLOAT,
#        COOL_SETPOINT FLOAT,
#        THERMOSTAT_STATE VARCHAR(4),
#        FAN_STATE VARCHAR(4),
#        IP_ADDRESS INET,
#        NICKNAME VARCHAR(30) NOT NULL,
#        ZONE_ID INT NOT NULL,
#        NETWORK_STATUS VARCHAR(7) NOT NULL,
#        OTHER_PARAMETERS VARCHAR(200),
#        LAST_SCANNED_TIME TIMESTAMP,
#        LAST_OFFLINE_TIME TIMESTAMP);''')
# print "Table thermostat created successfully"
# conn.commit()

cur.execute("select * from information_schema.tables where table_name=%s", ('supported_devices',))
print bool(cur.rowcount)
if bool(cur.rowcount):
    cur.execute("DROP TABLE supported_devices")
    conn.commit()
else:
    pass

cur.execute('''CREATE TABLE supported_devices
       (DEVICE_MODEL VARCHAR(30) PRIMARY KEY   NOT NULL,
       VENDOR_NAME  VARCHAR(50),
       COMMUNICATION VARCHAR(10),
       DEVICE_TYPE VARCHAR(20),
       DISCOVERY_TYPE VARCHAR(20),
       DEVICE_MODEL_ID  VARCHAR(5),
       API_NAME VARCHAR(50),
       IDENTIFIABLE BOOLEAN);''')
print "Table supported_devices created successfully"
conn.commit()

cur.execute("select * from information_schema.tables where table_name=%s", ('notification_event',))
print bool(cur.rowcount)
if bool(cur.rowcount):
    cur.execute("DROP TABLE notification_event")
    conn.commit()
else:
    pass

cur.execute('''CREATE TABLE notification_event
       (EVENT_ID SERIAL PRIMARY KEY   NOT NULL,
       EVENT_NAME  VARCHAR(30) NOT NULL,
       NOTIFY_DEVICE_ID  VARCHAR(50) NOT NULL,
       TRIGGERED_PARAMETER VARCHAR(20) NOT NULL,
       COMPARATOR VARCHAR(10) NOT NULL,
       THRESHOLD VARCHAR(10) NOT NULL,
       NOTIFY_CHANNEL VARCHAR(20) NOT NULL,
       NOTIFY_ADDRESS VARCHAR(30),
       NOTIFY_HEARTBEAT INT,
       DATE_ADDED TIMESTAMP,
       LAST_UPDATED TIMESTAMP);''')
print "Table notification_event created successfully"
conn.commit()

# Example of adding notification events of devices to a table
cur.execute("INSERT INTO notification_event VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (1,"high_temp","1NST18b4302964f1","temperature",">",75,"email","aribemoss@gmail.com",3600,datetime.datetime.now(),datetime.datetime.now()))
cur.execute("INSERT INTO notification_event VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (2,"low_temp","1NST18b4302964f1","temperature","<",70,"email","aribemoss@gmail.com",3600,datetime.datetime.now(),datetime.datetime.now()))
cur.execute("INSERT INTO notification_event VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (3,"low_battery","1NST18b4302964f1","battery","<",95,"email","aribemoss@gmail.com",3600,datetime.datetime.now(),datetime.datetime.now()))
conn.commit()

dummy_device_discovery = settings.DUMMY_SETTINGS['dummy_discovery']

print '!!!!!!!!!!!dummy_device_discovery!!!!!!!!!!!!!! '+str(dummy_device_discovery)

if dummy_device_discovery:
    cur.execute("INSERT INTO supported_devices VALUES(%s,%s,%s,%s,%s,%s,%s,%s)",
                ("CT30 V1.94","RadioThermostat","Dummy","thermostat","thermostat","1TH","classAPI_DummyRadioThermostat",True))
    cur.execute("INSERT INTO supported_devices VALUES(%s,%s,%s,%s,%s,%s,%s,%s)",
                ("CT50 V1.94","RadioThermostat","Dummy","thermostat","thermostat","1TH","classAPI_DummyRadioThermostat",True))
    cur.execute("INSERT INTO supported_devices VALUES(%s,%s,%s,%s,%s,%s,%s,%s)",
                ("Philips hue bridge 2012","Royal Philips Electronics","Dummy","lighting","Philips","2HUE","classAPI_DummyPhilipsHue",True))
    cur.execute("INSERT INTO supported_devices VALUES(%s,%s,%s,%s,%s,%s,%s,%s)",
                ("Socket","Belkin International Inc.","Dummy","plugload","WeMo_plugload","3WSP","classAPI_DummyWeMo",True))
    cur.execute("INSERT INTO supported_devices VALUES(%s,%s,%s,%s,%s,%s,%s,%s)",
                ("LightSwitch","Belkin International Inc.","Dummy","lighting","WeMo_lighting","2WL","classAPI_DummyWeMo",True))
    conn.commit()
else:
    print '!!!!!!!!!!!dummy_device_discovery!!!!!!!!!!!!!! else'
    cur.execute("INSERT INTO supported_devices VALUES(%s,%s,%s,%s,%s,%s,%s,%s)",
                ("CT30 V1.94","RadioThermostat","WiFi","thermostat","thermostat","1TH","classAPI_RadioThermostat",True))
    cur.execute("INSERT INTO supported_devices VALUES(%s,%s,%s,%s,%s,%s,%s,%s)",
                ("CT50 V1.94","RadioThermostat","WiFi","thermostat","thermostat","1TH","classAPI_RadioThermostat",True))
    cur.execute("INSERT INTO supported_devices VALUES(%s,%s,%s,%s,%s,%s,%s,%s)",
                ("Socket","Belkin International Inc.","WiFi","plugload","WeMo","3WSP","classAPI_WeMo",True))
    cur.execute("INSERT INTO supported_devices VALUES(%s,%s,%s,%s,%s,%s,%s,%s)",
                ("LightSwitch","Belkin International Inc.","WiFi","lighting","WeMo","2WL","classAPI_WeMo",True))
    cur.execute("INSERT INTO supported_devices VALUES(%s,%s,%s,%s,%s,%s,%s,%s)",
                ("Philips hue bridge 2012","Royal Philips Electronics","WiFi","lighting","Philips","2HUE","classAPI_PhilipsHue",True))
    conn.commit()
print "Table supported_devices populated successfully!"

# 9. close database connection
try:
    if conn:
        conn.close()
        print "{} >> Done 8: database {} connection is closed".format(agent_id, db_database)
except:
    print "{} >> database {} connection has already closed".format(agent_id, db_database)

# 10. clear volttron log file, kill volttron process, kill all BEMOSS processes
os.system("sudo chmod 777 -R ~/workspace/bemoss_os")
os.system("sudo rm ~/workspace/bemoss_os/volttron.log")
os.system("sudo killall volttron-lite")
os.system("sudo kill $(cat ~/workspace/bemoss_os/BEMOSS.pid)")
os.system("sudo rm ~/workspace/bemoss_os/BEMOSS.pid")
print "{} >> Done 9: clear volttron log file, kill volttron process, kill all " \
      "BEMOSS processes".format(agent_id)