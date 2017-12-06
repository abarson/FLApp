import watson_developer_cloud

YES = "yes"
NO  = "no"
LATE_FLIGHT = "late_flight"

class ConversationHelper():
    
    def __init__(self):
    #Constructor to initialize conversation tokens
        self.last_intent = ''
        self.conversation = watson_developer_cloud.ConversationV1(
            username = 'fe1f3935-fd7f-498e-8fc0-ac4260774df1',
            password = 'Z5xsGiNh3WbT',
            version  = '2017-12-05'
        )
        self.workspace_id = '296bb520-681b-4bcc-86f8-55c001aad75f'
        self.num_queries = 0
        self.context = {}


    def ask_watson(self, msg):
    #Call the Conversation API and return the results.
        self.num_queries+=1
        response = self.conversation.message(
            workspace_id = self.workspace_id,
            input = {
                'text': msg
            },
            context = self.context
        )
        return response

    def get_context(self, payload):
        return payload['context']
    
    def get_response(self, payload):
    #Takes user text and calls Watson API.
        return payload['output']['text'][0]
        
    def get_intent(self, payload):
        #print(response)
        if payload['intents']:
            intent = payload['intents'][0]['intent']
        else:
            intent = 'Unknown'
        return intent



