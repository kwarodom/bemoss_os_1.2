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
__lastUpdated__ = "2015-02-11 22:39:48"
'''

# settings file for BEMOSS project.

import os
import sys

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
     ('warodom', 'kwarodom@vt.edu'),
     ('avijit', 'avijit@vt.edu')
)

PROJECT_DIR = os.path.dirname(__file__)
Agents_DIR = os.path.join(PROJECT_DIR, 'Agents/')
Agents_Launch_DIR = os.path.join(PROJECT_DIR, 'Agents/LaunchFiles/')
Applications_DIR = os.path.join(PROJECT_DIR, 'bemoss/Applications/')
Applications_Launch_DIR = os.path.join(PROJECT_DIR, 'bemoss/Applications/launch/')
Loaded_Agents_DIR = os.path.expanduser("~/.config/volttron/lite/agents/")
Autostart_Agents_DIR = os.path.expanduser("~/.config/volttron/lite/autostart/")
Communications_DIR = os.path.join(PROJECT_DIR, 'bemoss/communication/')
Common_functions_DIR = os.path.join(PROJECT_DIR, 'bemoss/core/')
Custom_eggs_DIR = os.path.join(PROJECT_DIR, 'bemoss/custom-eggs/')

MANAGERS = ADMINS

PLATFORM = {
    'node': {
        'name': 'BEMOSS Core',
        'type': 'core',
        'model': 'MBP',
        'building_name': 'bemoss',
    }
}

DEVICES = {
    'device_monitor_time': 20
}

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',  # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'bemossdb',
        'USER': 'admin',
        'PASSWORD': 'admin',
        'HOST': 'localhost',
        'PORT': '5432',
        'TABLE_dashboard_device_info': 'dashboard_device_info',
        'TABLE_dashboard_current_status': 'dashboard_current_status',
        'TABLE_building_zone': 'building_zone',
        'TABLE_global_zone_setting': 'global_zone_setting',
        'TABLE_device_info': 'device_info',
        'TABLE_dashboard_building_zones': 'building_zone',
        'TABLE_holiday': 'holiday',
        'TABLE_application_running': 'application_running',
        'TABLE_application_registered': 'application_registered',
        'TABLE_plugload': 'plugload',
        'TABLE_thermostat': 'thermostat',
        'TABLE_lighting': 'lighting',
        'TABLE_device_metadata': 'device_metadata',
        'TABLE_supported_devices': 'supported_devices',
        'TABLE_notification_event': 'notification_event'
    }
}

NOTIFICATION = {
    'heartbeat': 24*60,  # heartbeat period to resend a message
    'heartbeat_device_tampering': 130,  # heartbeat period to resend a message
    'email': {
        'fromaddr': 'aribemoss@gmail.com',
        'recipients': ['aribemoss@gmail.com', 'trigger@ifttt.com'],
        'username': 'aribemoss@gmail.com',
        'password': 'DRTeam@900',
        'subject' : 'Message from',
        'mailServer': 'smtp.gmail.com:587'
    },
    'plugload':{
        'status': "ON",
        'power': 200
    },
    'thermostat':{
        'too_hot': 90,
        'too_cold': 60
    },
    'lighting':{
        'too_dark': 10  # % of brightness
    }
}

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
TIME_ZONE = 'America/New_York'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'b4nr@$=^2)_g!_vz-nm_1$_!!jfh&2yn$6#a9klqyh28g*vjl%'

FIND_DEVICE_SETTINGS = {
    'findWiFi': True,
    'findWiFiHue': True,
    'findWiFiWeMo': True,
}

DUMMY_SETTINGS = {
    'dummy_discovery': False,
    'number_of_hvac': 10,
    'number_of_lighting': 10,
    'number_of_plugload': 10,
}