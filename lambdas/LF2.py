import json
import boto3
from boto3.dynamodb.conditions import Key, Attr
import requests

def getSQS():
    SQS = boto3.client("sqs")
    url = 'SQS URL'
    response = SQS.receive_message(
        QueueUrl=url,
        AttributeNames=['SentTimestamp'],
        MessageAttributeNames=['All'],
        VisibilityTimeout=0,
        WaitTimeSeconds=10
    )
    print("Response from queue: ", response)
    try:
        message = response['Messages'][0]
        if message is None:
            print("Empty message")
            return None
    except KeyError:
        print("No message in the queue")
        return None
    message = response['Messages'][0]
    SQS.delete_message(
            QueueUrl=url,
            ReceiptHandle=message['ReceiptHandle']
        )
    print('Received and deleted message: %s' % response)
    print("message: {}".format(message))
    return message

def lambda_handler(event, context):

    message = getSQS()
    if message is None:
        print("No Cuisine or PhoneNum key found in message")
        return

    message_body = json.loads(message["Body"])
    print("cuisine: {}".format(message_body["Cuisine"]))
    party = message_body["NoOfPeople"]
    cuisine = message_body["Cuisine"]
    location = "Manhattan"
    phone = message_body["PhoneNumber"]
    time = message_body["Time"]
    date = message_body["Date"]
    
    if not cuisine or not phone:
        print("No Cuisine or Phone found in message")
        return
    print("Cuisine: {}, Phone number: {}, Time: {}, Date: {}, Number of people: {}".format(cuisine, phone, time, date, party))
    esUrl = "ELASTIC SEARCH URL"+cuisine
    esResponse = requests.get(esUrl, auth=("USER", "PASS"))

    
    print("esResponse: {}".format(esResponse.text))
    data = json.loads(esResponse.content.decode('utf-8'))
    
    try:
        esData = data["hits"]["hits"]
    except KeyError:
        print("Error extracting hits from ES response")

    resids = []
    for restaurant in esData:
        resids.append(restaurant["_source"]["Business ID"])
        
    print("Total ids: ", len(resids))
    
    messageToSend = 'Hello! Here are the {cuisine} restaurant suggestions in {location} for {numPeople} people, at {diningTime}: '.format(
            cuisine=cuisine,
            location=location,
            numPeople=party,
            diningTime=time,
        )

    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('yelp-restaurants')
    itr = 1 
    
    for id in resids:
        if itr == 4:
            break
        response = table.get_item(Key = {"Business ID": id})
        print("dynamodb response: {}".format(response))
        item = response['Item']
        name = item['name']
        address = item['address']
        if response is None:
            continue
        restaurantMsg = '' + str(itr) + '. '
        name = item["name"]
        address = item["address"]
        restaurantMsg += name +', located at ' + str(address)[1:-1] +'. '
        messageToSend += restaurantMsg
        itr += 1

    messageToSend += "Have a nice meal!!"
    print("messageToSend: {}".format(messageToSend))
    sns = boto3.client('sns', region_name='us-east-1')
    try:
        sns.publish(TopicArn='SNS TOPIC', Message=json.dumps(str(messageToSend)))
    except KeyError:
        print("Error sending ")
        sns.publish(TopicArn='SNS TOPIC', Message=json.dumps("Recommendations not found"))

    return {
        'statusCode': 200,
        'body': json.dumps(messageToSend)
    }