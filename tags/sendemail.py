#!/usr/bin/python

import smtplib
import threading
import os

email_address = os.environ["EMAIL_ADDRESS"]
email_password = os.environ["EMAIL_PASSWORD"]
to_email = os.environ["TO_EMAIL"]

def async(f):
    def wrapper(*args, **kwargs):
        thr = threading.Thread(target=f, args=args, kwargs=kwargs)
        thr.start()
    return wrapper

@async
def send_email(message):
    fullmessage = """\From: %s\nTo: %s\nSubject: Wikipedia Mining\n\n%s""" % (email_address, to_email, message)
    email_server = smtplib.SMTP_SSL('smtp.gmail.com')
    email_server.login(email_address, email_password)
    email_server.sendmail(email_address, to_email, fullmessage)
    email_server.close()

