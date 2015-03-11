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
__created__ = "2014-7-28 10:20:00"
__lastUpdated__ = "2015-02-11 19:27:31"
'''

# This Email class is for an agent wishing to send an email to any mail server

import smtplib  # simple mail transfer protocol library
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText

class EmailService:

    # method1: GET a model number of a device by XML read
    def sendEmail(self, fromaddr, recipients, username, password, subject, text, mailServer):
        try:
            # agent snippet to send notification to a building operator
            self.fromaddr = fromaddr
            self.recipients = recipients
            self.username = username
            self.password = password
            self.msg = MIMEMultipart()
            self.msg['From'] = self.fromaddr
            self.msg['To'] = ",".join(self.recipients)
            self.msg['Subject'] = subject
            self.text = text
            self.msg.attach(MIMEText(self.text))
            self.server = smtplib.SMTP(mailServer)
            self.server.ehlo()
            self.server.starttls()
            self.server.ehlo()
            self.server.login(self.username,self.password)
            self.server.sendmail(self.fromaddr, self.recipients, self.msg.as_string())
            self.server.quit()
            print("Email is sent successfully")
        except:
            print('Error: Connection with SMTP server failed')

# This main method will not be executed when this class is used as a module
def main():
    emailService = EmailService()
    emailService.sendEmail('aribemoss@gmail.com', ['aribemoss@gmail.com'], 'aribemoss@gmail.com', 'XXXXXXXX',
                           'Message from Email class', 'test Text', 'smtp.gmail.com:587')
if __name__ == "__main__": main()