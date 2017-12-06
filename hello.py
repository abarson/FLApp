from cloudant import Cloudant
from flask import Flask, render_template, request, jsonify
import atexit
import cf_deployment_tracker
import os
import json
import smtplib
from LittleBlueConversation import ConversationHelper
from email.mime.text import MIMEText 
import json

# Emit Bluemix deployment event
cf_deployment_tracker.track()

app = Flask(__name__)

conversation_helper = ConversationHelper()

db_name = 'mydb'
client = None
db = None


YES = "yes"
NO  = "no"
LATE_FLIGHT = "late_flight"

FROM_USER  = 'adam.barson'
FROM_EMAIL = 'adam.barson@gmail.com'
FROM_PASS  = 'coffeecoffee'

flight_details = {"FLIGHT_NO" : "A118",
                "DEP" : "Boston",
                "ARR" : "Austin",
                "DEP_TIME" : "05-18-2016 20:15",
                "ARR_TIME" : "05-18-2016 22:30"}

if 'VCAP_SERVICES' in os.environ:
    vcap = json.loads(os.getenv('VCAP_SERVICES'))
    print('Found VCAP_SERVICES')
    if 'cloudantNoSQLDB' in vcap:
        creds = vcap['cloudantNoSQLDB'][0]['credentials']
        user = creds['username']
        password = creds['password']
        url = 'https://' + creds['host']
        client = Cloudant(user, password, url=url, connect=True)
        db = client.create_database(db_name, throw_on_exists=False)
elif os.path.isfile('vcap-local.json'):
    with open('vcap-local.json') as f:
        vcap = json.load(f)
        print('Found local VCAP_SERVICES')
        creds = vcap['services']['cloudantNoSQLDB'][0]['credentials']
        user = creds['username']
        password = creds['password']
        url = 'https://' + creds['host']
        client = Cloudant(user, password, url=url, connect=True)
        db = client.create_database(db_name, throw_on_exists=False)

# On Bluemix, get the port number from the environment variable PORT
# When running this app on the local machine, default the port to 8000
port = int(os.getenv('PORT', 8000))

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/flights')
def flights():
    return render_template('flights.html')

@app.route('/little_blue_chat')
def litte_blue_chat():
    return render_template('chat.html')

@app.route('/contacts')
def contacts():
    return render_template('contacts.html')

# Endpoint to return rebooking details
@app.route('/details')
def details():
    return json.dumps(flight_details)

# /* Endpoint to greet and add a new visitor to database.
# * Send a POST request to localhost:8000/api/visitors with body
# * {
# *     "name": "Bob"
# * }
# */
@app.route('/api/visitors', methods=['GET'])
def get_visitor():
    if client:
        return jsonify(list(map(lambda doc: doc['name'], db)))
    else:
        print('No database')
        return jsonify([])

def send_email(recipients, msg):
#Helper method to send an email.

#recipients: a list of email addresses
#msg: a formatted message object

    server = smtplib.SMTP('smtp.gmail.com:587')
    server.ehlo()
    server.starttls()
    server.login(FROM_USER,FROM_PASS)
    server.sendmail(FROM_EMAIL, recipients, msg)
    server.quit()

def create_msg(msg_subject, msg_body):
#Helper method to format an the body of an email message

#@msg_subject: The subject of the email
#@msg_body: The body of the email

    return "\r\n".join([
          "Subject: {}".format(msg_subject),
          "",
          msg_body
          ])


@app.route('/api/messenger', methods=['POST'])
def messenger():
    msg = request.json['message']
    payload = conversation_helper.ask_watson(msg)

    print(conversation_helper.get_intent(payload))
    print(conversation_helper.get_response(payload))
    
    response = conversation_router(payload)
    return json.dumps({"response": response})
    
    

# /**
#  * Endpoint to get a JSON array of all the visitors in the database
#  * REST API example:
#  * <code>
#  * GET http://localhost:8000/api/visitors
#  * </code>
#  *
#  * Response:
#  * [ "Bob", "Jane" ]
#  * @return An array of all the visitor names
#  */
@app.route('/api/visitors', methods=['POST'])
def put_visitor():
    user = request.json['name']
    if client:
        data = {'name':user}
        db.create_document(data)
        return 'Hello %s! I added you to the database.' % user
    else:
        print('No database')

        print('Emailing user', user)
        send_email([user, 'adam.barson@gmail.com'],
                   create_msg("We're sorry", "Your flight is delayed"))
        
        return 'Hello %s!' % user



def conversation_router(payload):
    response = ''
    intent = conversation_helper.get_intent(payload)
    context = conversation_helper.get_context(payload)
    response = conversation_helper.get_response(payload)

    utterance = ''
    if intent == YES:
        if conversation_helper.last_intent == LATE_FLIGHT:
            utterance = ("Okay, I will email your contact list.")
        else:
            utterance = ("yes..?")
    elif intent == NO:
        if conversation_helper.last_intent == LATE_FLIGHT:
            utterance = ("Okay, I won't email your contact list.")
        else:
            utterance = ("no..?")
    elif intent == LATE_FLIGHT:
        utterance = (response)
    else:
        utterance = (response)

    conversation_helper.last_intent = intent
        
    return utterance


@atexit.register
def shutdown():
    if client:
        client.disconnect()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port, debug=True)
