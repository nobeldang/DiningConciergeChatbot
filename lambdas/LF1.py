import json
import datetime
import time
import os
import dateutil.parser
import boto3
import math

def sendMsg(slots):
    print("Inside sendMsg of LF1")
    sqs = boto3.client('sqs')
    queue_url = 'SQS URL'
    Attributes=json.dumps({
        'NoOfPeople': slots["NumberOfPeople"],
        'Date': slots["DiningDate"],
        'Time': slots["DiningTime"],
        'PhoneNumber': slots["PhoneNumber"],
        'Cuisine': slots["Cuisine"]
        })
    print("Attribute type: ", type(Attributes))
    print("Attributes: ", Attributes)
    response = sqs.send_message(
        QueueUrl=queue_url,
        DelaySeconds=5,
        MessageBody=Attributes,
        MessageAttributes={
            'MessageType': {
                'StringValue': 'GetSuggestionsForDining',
                'DataType': 'String'
                }
            }
        )

    print("Sent response to queue is: ", response)

def elicit_slot(session_attributes, intent_name, slots, slot_to_elicit, message):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'ElicitSlot',
            'intentName': intent_name,
            'slots': slots,
            'slotToElicit': slot_to_elicit,
            'message': message
        }
    }


def confirm_intent(session_attributes, intent_name, slots, message):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'ConfirmIntent',
            'intentName': intent_name,
            'slots': slots,
            'message': message
        }
    }


def close(session_attributes, fulfillment_state, message):
    response = {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Close',
            'fulfillmentState': fulfillment_state,
            'message': message
        }
    }
    return response


def delegate(session_attributes, slots):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Delegate',
            'slots': slots
        }
    }


# --- Helper Functions ---


def safe_int(n):
    if n is not None:
        return int(n)
    return n


def try_ex(func):
    try:
        return func()
    except KeyError:
        return None

##########################################################################################################################

def build_validation_result(isvalid, violated_slot, message_content):
    return {
        'isValid': isvalid,
        'violatedSlot': violated_slot,
        'message': {'contentType': 'PlainText', 'content': message_content}
    }



def parse_int(n):
    try:
        return int(n)
    except ValueError:
        return float('nan')
        
def isvalid_cuisine(cuisine):
    cuisines = ['indian', 'thai', 'mediterranean', 'chinese', 'italian']
    return cuisine.lower() in cuisines

def isvalid_numberofpeople(numPeople):
    numPeople = safe_int(numPeople)
    return True
        
def isvalid_date(diningdate):
    try:
        dateutil.parser.parse(diningdate)
        parsed = datetime.datetime.strptime(diningdate, '%Y-%m-%d').date()
        if parsed < datetime.date.today():
            return False
        return True
    except ValueError:
        return False


def isvalid_time(diningdate, diningtime):
    if datetime.datetime.strptime(diningdate, '%Y-%m-%d').date() == datetime.date.today():
        if datetime.datetime.strptime(diningtime, '%H:%M').time() <= datetime.datetime.now().time():
            return False

def validate_dining_suggestion(cuisine, numPeople, diningdate, diningtime, phonenumber):
    if cuisine is not None:
        if not isvalid_cuisine(cuisine):
            return build_validation_result(False, 'Cuisine', 'Cuisine not available. Please try another.')
            
    if diningdate is not None:
        if not isvalid_date(diningdate):
            return build_validation_result(False, 'DiningDate', 'Please enter valid date')
    
    if diningtime is not None and diningdate is not None:
        print("DINING LOGS: ### {} {}".format(diningdate, diningtime))
        
        if len(diningtime) != 5:
            return build_validation_result(False, 'DiningTime', None)

        hour, minute = diningtime.split(':')
        hour = parse_int(hour)
        minute = parse_int(minute)
        if math.isnan(hour) or math.isnan(minute):
            return build_validation_result(False, 'DiningTime', None)

        if hour < 10 or hour > 24:
            return build_validation_result(False, 'DiningTime', 'Business hours are from 10 AM to 11 PM. Please enter time duringin between this range?')

        
    if numPeople is not None and not numPeople.isnumeric():
        return build_validation_result(False,
                                       'NumberOfPeople',
                                       'That does not look like a valid number {}, '
                                       'Could you please repeat?'.format(numPeople))
    
    if phonenumber is not None and not phonenumber.isnumeric():
        return build_validation_result(False,
                                       'PhoneNumber',
                                       'That does not look like a valid number {}, '
                                       'Could you please repeat? '.format(phonenumber))    
    return build_validation_result(True, None, None)





def greetings(intent_request):
    return {
        'dialogAction': {
            "type": "ElicitIntent",
            'message': {
                'contentType': 'PlainText',
                'content': 'Hi there, how can I help?'}
        }
    }

def thank_you(intent_request):
    return {
        'dialogAction': {
            "type": "ElicitIntent",
            'message': {
                'contentType': 'PlainText',
                'content': 'You are welcome!'}
        }
    }

def dining_suggestions(intent_request):
    slots = intent_request['currentIntent']['slots']
    location = slots["location"]
    cuisine = slots["Cuisine"]
    numPeople = slots["NumberOfPeople"]
    diningdate = slots["DiningDate"]
    diningtime = slots["DiningTime"]
    phonenumber = slots["PhoneNumber"]
    
    
    if intent_request['invocationSource'] == 'DialogCodeHook':
        validation_result = validate_dining_suggestion(cuisine, numPeople, diningdate, diningtime, phonenumber)
        if not validation_result['isValid']:
            slots[validation_result['violatedSlot']] = None
            return elicit_slot(intent_request['sessionAttributes'],
                               intent_request['currentIntent']['name'],
                               slots,
                               validation_result['violatedSlot'],
                               validation_result['message'])
    
        if intent_request[
                'sessionAttributes'] is not None:
                output_session_attributes = intent_request['sessionAttributes']
        else:
            output_session_attributes = {}
        return delegate(output_session_attributes, intent_request['currentIntent']['slots'])
    
    sendMsg(slots)
    return close(intent_request['sessionAttributes'],
                 'Fulfilled',
                 {'contentType': 'PlainText',
                  'content': 'Thank you! You will recieve suggestion shortly via email'})
    



# --- Intents ---


def dispatch(intent_request):
    intent_name = intent_request['currentIntent']['name']

    # INTENT PASSED TO BOT
    if intent_name == 'DiningSuggestionsIntent':
        return dining_suggestions(intent_request)
    elif intent_name == 'GreetingIntent':
        return greetings(intent_request)
    elif intent_name == 'ThankYouIntent':
        return thank_you(intent_request)

    raise Exception('Intent with name ' + intent_name + ' not supported')


def lambda_handler(event, context):
    os.environ['TZ'] = 'America/New_York'
    time.tzset()

    return dispatch(event)