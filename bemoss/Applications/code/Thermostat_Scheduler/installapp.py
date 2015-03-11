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
__lastUpdated__ = "2015-02-11 19:23:46"
'''

import os
from setuptools import find_packages
import sys
import psycopg2  # PostgresQL database adapter
import time
import datetime

#APP CONFIGURATION-------------------------------------------------------------------------------
#TODO change auth_token
auth_token = 'bemoss'
#TODO change description
app_description = 'Scheduling APP to control thermostat'
#TODO change app_user
app_user = ["thermostat"]
#------------------------------------------------------------------------------------------------

app_name = find_packages('.')
app_name = app_name[0]
# print app_name
app_exec = app_name+'agent-0.1-py2.7.egg'
exec_store = app_name + 'agent'
# print app_exec
app_working_directory = os.getcwd()
app_folder = os.path.basename(os.getcwd())
os.chdir(os.path.expanduser("~/workspace/bemoss_os/"))  # = ~/workspace/bemoss_os
# os.chdir("../../../../")
current_working_directory = os.getcwd()
# print 'current working directory: {}'.format(_current_working_directory)
#import settings.py file to get database information
sys.path.append(current_working_directory)
import settings

# @params agent & DB interfaces
db_host = settings.DATABASES['default']['HOST']
db_port = settings.DATABASES['default']['PORT']
db_database = settings.DATABASES['default']['NAME']
db_user = settings.DATABASES['default']['USER']
db_password = settings.DATABASES['default']['PASSWORD']
db_table_application_registered = settings.DATABASES['default']['TABLE_application_registered']

try:
    con = psycopg2.connect(host=db_host, port=db_port, database=db_database, user=db_user,
                                password=db_password)
    cur = con.cursor()  # open a cursor to perfomm database operations
    print("APP Installer >> connects to the database name {} successfully".format(db_database))
except:
    print("APP Installer >> ERROR: {} fails to connect to the database name {}".format(app_name, db_database))

cur.execute("SELECT executable FROM "+db_table_application_registered+" WHERE app_name=%s", (app_name,))
if cur.rowcount != 0:  # app has already been installed and registered
    print("APP Installer >> the APP name {} exists, this process will re-install the APP".format(app_name))
    cur.execute("DELETE FROM "+db_table_application_registered+" WHERE app_name=%s", (app_name,))
else:  # go ahead and add this app to database
    pass

# print app_folder
print 'APP Installer >> installing APP name {}, in folder {}, with exec {} ...'.format(app_name, app_folder, app_exec)
# print 'current working directory: {}'.format(_current_working_directory)
os.system("sudo bin/volttron-lite -c dev-config.ini -v -v &")
time.sleep(1)
os.system("sudo rm bin/"+app_exec)
os.system("sudo rm bemoss/Applications/egg/"+app_exec)
os.system("sudo volttron/scripts/build-app2.sh "+app_folder)
os.system("sudo bin/volttron-ctrl install-executable bemoss/Applications/egg/" + app_exec)
print '-----------------------------------------------------'
print 'APP name {}, in folder {}, with exec {} is installed successfully'.format(app_name, app_folder, app_exec)
print '-----------------------------------------------------'
os.system("sudo chmod 777 -R "+app_working_directory)
cur.execute("SELECT application_id FROM "+db_table_application_registered)
if cur.rowcount != 0:
    # print 'cur.fetchall()' + str(max(cur.fetchall())[0])
    app_no = max(cur.fetchall())[0] + 1
else: #default no_app
    app_no = 1
registered_time = str(datetime.datetime.now())
last_updated_time = str(datetime.datetime.now())
cur.execute("INSERT INTO application_registered(application_id, app_name, executable, auth_token, app_user, "
            "description,registered_time,last_updated_time) VALUES(%s,%s,%s,%s,%s,%s,%s,%s)",
            (app_no, app_name, exec_store, auth_token, str(app_user), app_description, registered_time, last_updated_time))
con.commit()
os.system("sudo killall volttron-lite")