from flask import Flask, request, send_from_directory, redirect, render_template, session, Response, jsonify
from twilio.twiml.messaging_response import MessagingResponse, Message
from twilio.rest import Client
from datetime import date

#import redis

# Your Account SID from twilio.com/console
account_sid = "<SECRET_SID>"
auth_token  = "<SECRET_TOKEN>"
client = Client(account_sid, auth_token)

# set the project root directory as the static folder, you can set others.
app = Flask(__name__, static_url_path='')
glob_messages = []

#red = redis.StrictRedis(host='redis-12928.c14.us-east-1-2.ec2.cloud.redislabs.com', port=12928, db=0)

#def event_stream():
#    pubsub = red.pubsub()
#    pubsub.subscribe('notifications')
#    #yield 'data: %s\n\n' % '111'
#    for message in pubsub.listen():
#        print message
#        yield 'data: %s\n\n' % message['data']

@app.route('/post', methods=['POST'])
def post():
    #red.publish('notifications', 'Hello!')
    #return redirect('/')
    return True

#@app.route('/stream')
#def stream():
#    return Response(event_stream(), mimetype="text/event-stream")

@app.route('/')
def index():
    return '''
<html>
<head>
<style type="text/css">
	.messages {
		border: 1px solid lightgrey;
		margin-bottom: 5px;
		overflow-y: scroll;
		padding: 5px;
		text-align: center;
		font-size: 25pt;
	}
</style>
<script type="text/javascript" src="https://cdnjs.cloudflare.com/ajax/libs/jquery/3.2.1/jquery.min.js"></script>
</head>
<body>
    <!--div id="messages_id" class="microsoft container" style="height: 500px;"></div-->
    <marquee id="messages_id" behavior="scroll" direction="up" class="messages" style="height:500px;">
	</marquee>
    <script>
    var analytics = document.getElementById('messages_id');
    (function poll(){
        $.ajax({ url: "/messages", success: function(data){
            console.log('called');
            var divContent = "";
            var messagesArray = data.messages;
            var arrayLength = messagesArray.length;
			for (var i = 0; i < arrayLength; i++) {
				divContent = divContent.concat("<p class='marquee'>");
				divContent = divContent.concat(messagesArray[i]);
				divContent = divContent.concat("</p>");
				//divContent = divContent.concat("<br>");
			}
			//console.log(divContent);
            analytics.innerHTML = divContent;
        }, dataType: "json", complete: setTimeout(poll,3000), timeout: 30000 });
    })();
    </script>
</body>
</html>


'''

@app.route('/messages')
def hello_world():
    res = []
    all_messages = client.messages.list(date_sent=date(2017,6,5)) + client.messages.list(date_sent=date(2017,6,4))
    for message in reversed(all_messages):
        if message.direction == 'inbound':
            res.append(message.body)
    msg = {'messages': res}
    return jsonify(msg)
    #return 'Hello, World!' + str(res)

@app.route('/js/<path:path>')
def send_js(path):
    return send_from_directory('js', path)

@app.route('/html/<path:path>')
def send_html(path):
    return send_from_directory('html', path)

@app.route("/sms_recv", methods=['GET', 'POST'])
def hello_monkey():
    global glob_messages
    from_number = request.values.get('From', None)
    body = request.values.get('Body', None)
    glob_messages.append(body)
    resp = MessagingResponse()
    msg = Message().body("Hello, Mobile Monkey 2!")
    #.media("/html/jch-90th-header-new.jpg")
    resp.append(msg)
    return str(resp)

if __name__ == "__main__":
    app.debug = True
    #app.threaded=True
    app.run(host='0.0.0.0',port=3001)
    #app.run(debug=True)
    #app.run(threaded=True)
