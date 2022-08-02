#!/usr/bin/env python
# coding: utf-8


import requests
from decimal import *
import datetime
import json
import boto3
import datetime
import requests
from decimal import *
from time import sleep
import pandas as pd
from requests_aws4auth import AWS4Auth
from elasticsearch import Elasticsearch, RequestsHttpConnection

url = 'https://api.yelp.com/v3/businesses/search'
key = 'YELP ACCOUNT KEY'


headers = {
    'Authorization': 'Bearer '+key
}
cuisines = ['chinese', 'italian', 'indian', 'mexican', 'thai', 'american']

restaurants = []
commonIdx = set([])
for cuisine in cuisines:
    for i in range(0, 1000, 50):
        parameters = {'term': cuisine,
                 'location': 'Manhattan',
                 'offset': i,
                 'limit': 50
                }
        response = requests.get(url, headers = headers, params = parameters)
        if 'businesses' not in response.json().keys():
            continue
        restaurantsBatch = response.json()['businesses']
        for j in restaurantsBatch:
            if j['id'] in commonIdx:
                continue
            j['cuisine'] = cuisine
            restaurants.append(j)
            commonIdx.add(j['id'])
    print(len(restaurants))

restaurantData = []
for j in restaurants:
    res ={} 
    res['Business ID'] = j['id']
    res['name'] = j['name']  
    res['address'] = j['location']['display_address']
    res['coordinates'] = {}
    res['coordinates']['latitude'] = Decimal(str(j['coordinates']['latitude']))
    res['coordinates']['longitude'] = Decimal(str(j['coordinates']['longitude']))
    res['reviews'] = j['review_count']
    res['rating'] = Decimal(j['rating'])
    res['zip'] = j['location']['zip_code']
    res['cuisine'] = j['cuisine']
    restaurantData.append(res)


client = boto3.resource(service_name='dynamodb',
                          aws_access_key_id="ACCESS KEY",
                          aws_secret_access_key="SECRET KEY",
                          region_name="us-east-1",
                         )
table = client.Table('yelp-restaurants')

def addItems(data):
    with table.batch_writer() as batch:
        for rec in data:
            try:
                rec['insertedAtTimestamp'] = str(datetime.datetime.now())
                batch.put_item(Item=rec)
                sleep(0.001)
            except Exception as e:
                print(e)
                print(rec)

for i in range(0, len(restaurantData), 20):
    if i==4980:
        addItems(restaurantData[i:])
        break
    addItems(restaurantData[i:i+20])


## Putting Data in Elastic Search

region = 'us-east-1'
service = 'es'
credential = boto3.Session(aws_access_key_id="ACCESS KEY",
                          aws_secret_access_key="SECRET KEY", 
                          region_name=region).get_credentials()
auth = AWS4Auth(credential.access_key, credential.secret_key, region, service)


esEndPoint = "ES URL"

# taken from stack overflow
es = Elasticsearch(
    hosts = [{'host': esEndPoint, 'port': 443}],
    http_auth = auth,
    use_ssl = True,
    verify_certs = True,
    connection_class = RequestsHttpConnection
)
es.info()
es.ping()

restaurants = {}
def addItemsES(data):
    for rec in data:
            dataToAdd = {}
            try:
                dataToAdd['cuisine'] = rec['cuisine']
                dataToAdd['Business ID'] = rec['Business ID']
                sleep(0.001)
                es.index(index="restaurants", doc_type="Restaurants", body=dataToAdd)
            except Exception as e:
                print(e)

for i in range(0, len(restaurantData), 20):
    if i==4980:
        addItemsES(restaurantData[i:])
        break
    addItemsES(restaurantData[i:i+20])
print("Added successfully")