from cloudant import Cloudant
from flask import Flask, render_template, request, jsonify
import atexit
import cf_deployment_tracker
import os
import json
import smtplib
from LittleBlueConversation import ConversationHelper
from email.mime.text import MIMEText 

# Emit Bluemix deployment event
cf_deployment_tracker.track()

app = Flask(__name__)

conversation_helper = ConversationHelper()

db_name = 'mydb'
client = None
db = None

FROM_USER  = 'adam.barson'
FROM_EMAIL = 'adam.barson@gmail.com'
FROM_PASS  = 'coffeecoffee'

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

@app.route('/chat')
def chat():
    return render_template('chat.html')

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
    response = conversation_helper.process_message(msg)
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

@atexit.register
def shutdown():
    if client:
        client.disconnect()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port, debug=True)
