from flask import Flask, request, send_from_directory, redirect, render_template, session, Response, jsonify, url_for
from flask_sqlalchemy import SQLAlchemy
from twilio.twiml.messaging_response import MessagingResponse, Message
from twilio.rest import Client
from datetime import date
from datetime import timedelta
from collections import Counter
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

@app.template_filter()
def datetimefilter(value, format='%Y/%m/%d %H:%M'):
    return value.strftime(format)

app.jinja_env.filters['datetimefilter'] = datetimefilter

app.config["DEBUG"] = True

SQLALCHEMY_DATABASE_URI = "mysql+mysqlconnector://{username}:{password}@{hostname}/{databasename}".format(
    username=os.environ["MYSQL_USER"],
    password=os.environ["MYSQL_PASS"],
    hostname=os.environ["MYSQL_HOST"],
    databasename="notna2000$comments",
)
app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
app.config["SQLALCHEMY_POOL_RECYCLE"] = 299
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Comment(db.Model):

    __tablename__ = "comments"

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(4096))

def hasNumbers(inputString):
    return any(char.isdigit() for char in inputString)

def get_messages():
    today = date.today()
    tomorrow = today + timedelta(days=1)
    yesterday = today - timedelta(days=1)
    all_messages = client.messages.list(date_sent=today) + client.messages.list(date_sent=tomorrow) + client.messages.list(date_sent=yesterday)
    return all_messages

def get_conversation(num):
    conv = client.messages.list(to=num) + client.messages.list(from_=num)
    conv.sort(key=lambda x: x.date_sent, reverse=True)
    return conv

def delete_messages():
    all_messages = get_messages()
    for message in all_messages:
        client.messages(message.sid).delete()

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

'''Files to watch in order to restart webserver when they change for local dev'''
def get_files_to_watch():
    extra_dirs = ['./templates',]
    extra_files = extra_dirs[:]
    for extra_dir in extra_dirs:
        for dirname, dirs, files in os.walk(extra_dir):
            for filename in files:
                filename = os.path.join(dirname, filename)
                if os.path.isfile(filename):
                    extra_files.append(filename)
    return extra_files

@app.route('/')
def index():
    return redirect("/html/index.html", code=302)

@app.route("/notna", methods=["GET", "POST"])
def notna():
    if request.method == "GET":
        return render_template("main_page.html", comments=Comment.query.all())

    comment = Comment(content=request.form["contents"])
    db.session.add(comment)
    db.session.commit()
    return redirect(url_for('notna'))

@app.route("/conversation", methods=["GET", "POST"])
def conversation():
    if request.method == "GET":
        from_ = request.args.get('from_', '')
        return render_template("conversation.html", texts=get_conversation(from_), from_=from_.strip())

    from_ = request.form["from_"]
    client.messages.create(to=from_,from_=from_num,body=request.form["contents"])
    return render_template("conversation_content.html", texts=get_conversation(from_), from_=from_.strip())


@app.route("/conversation_content", methods=["GET"])
def conversation_content():
    from_ = request.args.get('from_', '')
    return render_template("conversation_content.html", texts=get_conversation(from_), from_=from_)


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
    bodies = []
    cnt_res = []
    all_messages = get_messages()
    for message in all_messages:
        if message.direction == 'inbound':
            bodies.append(message.body)
            o = {   'sid': message.sid,
                    'body': message.body,
                    'from_': message.from_,
                    'date_sent': message.date_sent
            };
            res.append(o)

    cnt_res = [{'text': w[0], 'count': w[1]} for w in Counter(bodies).most_common()]
    msg = {'messages': res, 'count': cnt_res }
    return jsonify(msg)

@app.route('/message_delete')
def message_delete():
    sid = request.args.get('sid', '')
    client.messages(sid).delete()
    return 'OK'

@app.route('/message_delete_all')
def message_delete_all():
    delete_messages()
    return 'Deleted all Messages!'

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

    msg = {'messages': res, 'total': sum(tot_res), 'count': Counter(res) }
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
    #Uncomment to echo the messages to some number
    #send_message(str(from_number)+':'+body)
    if hasNumbers(body):
        response_text = "Thank you for supporting the JCH on it's 90th Anniversary. You can complete your pledge here: http://www.jchb.org/donate/#online or a staff will contact you to fulfill your pledge"
    else:
        response_text = "Thank you for supporting the JCH on it's 90th Anniversary."

    response_text = "Thanks for participating and attending my talk @ QCon New York!"
#    if body.lower() == 'subscribe':
#        response_text = "Thank you for subscribing, you'll be receiving updates throughout the event. Text STOP to unsubscribe."
    
    #Uncomment to send responses back to user.
    # resp = MessagingResponse()
    # msg = Message().body(response_text)
    # #.media("/html/jch-90th-header-new.jpg")
    # resp.append(msg)
    # return str(resp)
    return 'OK'

if __name__ == "__main__":
    app.run(host='0.0.0.0',port=3001,extra_files=get_files_to_watch())
