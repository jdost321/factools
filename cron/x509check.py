#!/usr/bin/env python
'''

Check the expriation date of an X.509 certificate and compare its 
expiration date against today's date. If the expiration date is at 
T-minus X days out (or if the certificate has already expired), then 
send an email notification to a list of recipients warning them about 
the impending expiration of the certificate.

'''

import os
import sys
import string
import datetime
import subprocess
import smtplib
import re

def send_email(host, sender, recipients, subject, body):
    smtpObj = smtplib.SMTP(host)
    smtpObj.ehlo() # TODO: add exception handling
    message = string.join(('From: %s' % sender, 
                           'To: %s' % ', '.join(recipients),
                           'Subject: %s' % subject ,
                           '',
                           body), '\r\n')
    smtpObj.sendmail(sender, recipients, message)
    smtpObj.quit()

def main():
    # Get path to certificate
    x509_file_path = ''
    x509_file_path = sys.argv[1]

    # Read and parse subject DN of certificate
    x509_subject = ''
    x509_subject = subprocess.Popen(['openssl', 'x509', '-in', x509_file_path, '-noout', '-subject'], stdout=subprocess.PIPE).communicate()[0]
    x509_subject = re.sub('subject= ', '', x509_subject)
    x509_subject = re.sub('(\n)$', '', x509_subject)

    # Read and parse certificate's expiration date, then convert to date object
    x509_exp_date = ''
    x509_exp_date = subprocess.Popen(['openssl', 'x509', '-in', x509_file_path, '-noout', '-enddate'], stdout=subprocess.PIPE).communicate()[0]
    x509_exp_date = re.sub('notAfter=', '', x509_exp_date)
    x509_exp_date = re.sub(' (\D{3}\n)$', '', x509_exp_date)
    x509_exp_datetime = datetime.datetime.strptime(x509_exp_date, '%b %d %H:%M:%S %Y')
    x509_exp_dateonly = datetime.datetime.date(x509_exp_datetime)

    # Get today's date object
    now_datetime = datetime.datetime.now()
    today_date = datetime.datetime.date(now_datetime)

    # Construct email address of user who sends notifications 
    user = os.environ['USER']
    hostname = os.environ['HOSTNAME']
    sender = user + '@' + hostname

    # Get email addresses for recipients who receive notifications
    recipients = []
    for i in range(2, len(sys.argv)):
        recipients.append(sys.argv[i])

    # Check if X.509 certifiacte will expire soon. If so, send email 
    # notifications to list of recipients.
    if today_date < x509_exp_dateonly:
        t_minus_days = [20, 10, 5, 2, 1]
        for x in t_minus_days:
            if today_date == x509_exp_dateonly - datetime.timedelta(days = x):
                subject = 'WARNING: X.509 certificate on ' + hostname + ' will expire in ' + str(x) + ' days.'
                body = 'Dear overlords,\n\nMy X.509 certificate [1] will expire on ' + x509_exp_dateonly.strftime('%A, %B %d') + '. The subject DN of this certificate is [2]. Please renew the certificate as soon as possible.\n\nSincerely,\n\n' + hostname + '\n\n[1]\n\n' + x509_file_path + '\n\n[2]\n\n' + x509_subject
                send_email('localhost', sender, recipients, subject, body)
    else: 
        subject = 'URGENT: X.509 certificate on ' + hostname + ' has EXPIRED!'
        body = 'Overlords!\n\nMy X.509 certificate [1] EXPIRED on ' + x509_exp_dateonly.strftime('%A, %B %d') + '! The subject DN of this certificate is [2]. Please renew the certificate NOW!\n\nSincerely,\n\n' + hostname + '\n\n[1]\n\n' + x509_file_path + '\n\n[2]\n\n' + x509_subject
        send_email('localhost', sender, recipients, subject, body)

    return 0

if __name__ == '__main__':
    sys.exit(main())
