import watson_developer_cloud

class ConversationHelper():

    def __init__(self):
    #Constructor to initialize conversation tokens
        self.conversation = watson_developer_cloud.ConversationV1(
            username = 'fe1f3935-fd7f-498e-8fc0-ac4260774df1',
            password = 'Z5xsGiNh3WbT',
            version  = '2017-12-05'
        )
        self.workspace_id = '296bb520-681b-4bcc-86f8-55c001aad75f'
        self.num_queries = 0

    def process_message(self, msg):
    #Takes user text and calls Watson API.
        self.num_queries+=1
        print(self.num_queries)
        response = self.conversation.message(
            workspace_id = self.workspace_id,
            input = {
                'text': msg
            }
        )
        if response['output']['text']:
            print(response)
            print(response['output']['text'][0])

#helper = ConversationHelper()
#helper.process_message("My flight is late!")



