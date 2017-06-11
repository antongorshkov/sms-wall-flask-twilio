from twilio.rest import Client
from datetime import date
from datetime import timedelta
#from flask import jsonify
#import json
import os

# Your Account SID from twilio.com/console
account_sid = os.environ["TWILIO_SID"]
auth_token  = os.environ["TWILIO_TOKEN"]
to_num  = os.environ["DEFAULT_TO"]
from_num  = os.environ["DEFAULT_FROM"]

client = Client(account_sid, auth_token)

def get_messages():
    today = date.today()
    tomorrow = today + timedelta(days=1)
    all_messages = client.messages.list(date_sent=today) + client.messages.list(date_sent=tomorrow)
    return all_messages

def show_messages():
    all_messages = get_messages()
    for message in all_messages:
        if message.direction == 'inbound':
            print(message.body)

def delete_messages():
    all_messages = get_messages()
    for message in all_messages:
        client.messages(message.sid).delete()

def send_message():
    message = client.messages.create(
        to=to_num,
        from_=from_num,
        body="Hello from Python!")

def messages_details():
    res = []
    all_messages = get_messages()
    for message in all_messages:
        if message.direction == 'inbound':
            o = {   'sid': message.sid,
                    'body': message.body,
                    'from_': message.from_,
                    'date_sent': message.date_sent
            };
            res.append(o)

    msg = {'messages': res }
    print(msg)
    print(dir(message))
    return msg

#delete_messages()
#show_messages()
#send_message()
messages_details()
