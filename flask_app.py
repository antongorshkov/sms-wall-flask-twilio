from flask import Flask, request, send_from_directory, redirect, render_template, session, Response, jsonify
from twilio.twiml.messaging_response import MessagingResponse, Message
from twilio.rest import Client
from datetime import date
from datetime import timedelta
import json
import os

# Your Account SID from twilio.com/console
account_sid = os.environ["TWILIO_SID"]
auth_token  = os.environ["TWILIO_TOKEN"]
to_num  = os.environ["DEFAULT_TO"]
from_num  = os.environ["DEFAULT_FROM"]

client = Client(account_sid, auth_token)

# set the project root directory as the static folder, you can set others.
app = Flask(__name__, static_url_path='')

def hasNumbers(inputString):
    return any(char.isdigit() for char in inputString)

def get_messages():
    today = date.today()
    tomorrow = today + timedelta(days=1)
    yesterday = today - timedelta(days=1)
    all_messages = client.messages.list(date_sent=today) + client.messages.list(date_sent=tomorrow) + client.messages.list(date_sent=yesterday)
    return all_messages

def get_subs():
    res = []
    all_messages = get_messages()
    for message in reversed(all_messages):
        if message.direction == 'inbound' and message.body.lower() == 'subscribe':
            res.append(message.from_)
    return res

def send_message(msg):
    message = client.messages.create(
        to=to_num,
        from_=from_num,
        body=msg)

@app.route('/')
def index():
    return redirect("/html/index.html", code=302)

@app.route("/notna")
def notna():
    return render_template("main_page.html")

@app.route('/total')
def total():
    res = []
    all_messages = get_messages()
    for message in reversed(all_messages):
        if message.direction == 'inbound' and message.body.lower() != 'subscribe':
            res.append(sum([int(s) for s in message.body.split() if s.isdigit()]))
    msg = {'total': sum(res)}
    return jsonify(msg)

@app.route('/messages_details')
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
    return jsonify(msg)

@app.route('/message_delete')
def message_delete():
    sid = request.args.get('sid', '')
    client.messages(sid).delete()
    return 'OK'

@app.route('/messages')
def hello_world():
    res = []
    tot_res = []
    today = date.today()
    tomorrow = today + timedelta(days=1)
    all_messages = client.messages.list(date_sent=today) + client.messages.list(date_sent=tomorrow)
    for message in reversed(all_messages):
        if message.direction == 'inbound' and message.body.lower() != 'subscribe':
            res.append(message.body)
            tot_res.append(sum([int(s) for s in message.body.split() if s.isdigit()]))

    msg = {'messages': res, 'total': sum(tot_res) }
    return jsonify(msg)

@app.route('/subs')
def subscribers():
    res = get_subs()
    msg = {'subs': res}
    return jsonify(msg)

@app.route('/js/<path:path>')
def send_js(path):
    return send_from_directory('js', path)

@app.route('/html/<path:path>')
def send_html(path):
    return send_from_directory('html', path)

@app.route("/sms_recv", methods=['GET', 'POST'])
def hello_monkey():
    from_number = request.values.get('From', None)
    body = request.values.get('Body', None)
    send_message(str(from_number)+':'+body)
    if hasNumbers(body):
        response_text = "Thank you for supporting the JCH on it's 90th Anniversary. You can complete your pledge here: http://www.jchb.org/donate/#online or a staff will contact you to fulfill your pledge"
    else:
        response_text = "Thank you for supporting the JCH on it's 90th Anniversary."

#    if body.lower() == 'subscribe':
#        response_text = "Thank you for subscribing, you'll be receiving updates throughout the event. Text STOP to unsubscribe."
    resp = MessagingResponse()
    msg = Message().body(response_text).media("/html/jch-90th-header-new.jpg")
    resp.append(msg)
    return str(resp)

if __name__ == "__main__":
    app.debug = True
    app.run(host='0.0.0.0',port=3001)
