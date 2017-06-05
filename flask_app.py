from flask import Flask, request, send_from_directory, redirect, render_template, session, Response, jsonify
from twilio.twiml.messaging_response import MessagingResponse, Message
from twilio.rest import Client
from datetime import date

# Your Account SID from twilio.com/console
account_sid = "<SECRET>"
auth_token  = "<SECRET>"
client = Client(account_sid, auth_token)

# set the project root directory as the static folder, you can set others.
app = Flask(__name__, static_url_path='')

@app.route('/')
def index():
    return redirect("index.html", code=302)

@app.route('/messages')
def hello_world():
    res = []
    all_messages = client.messages.list(date_sent=date(2017,6,5)) + client.messages.list(date_sent=date(2017,6,4))
    for message in reversed(all_messages):
        if message.direction == 'inbound':
            res.append(message.body)
    msg = {'messages': res}
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
    resp = MessagingResponse()
    msg = Message().body("Hello, Mobile Monkey 2!")
    #.media("/html/jch-90th-header-new.jpg")
    resp.append(msg)
    return str(resp)

if __name__ == "__main__":
    app.debug = True
    app.run(host='0.0.0.0',port=3001)
