# Dining Concierge Chatbot
It is a serverless, microservice-driven web application built using AWS. The Dining Concierge chatbot based web application sends restaurant suggestions given a set of preferences that we provide the chatbot with through conversation.

The restaurants' metadata is taken from YELP api.

# Web Application:

<img src = "https://user-images.githubusercontent.com/26826339/190945930-e66b874b-fd06-48bc-baca-69b6c36442c2.png" width="700" height="500" />

# Services Used:
1) AWS S3 - To host web application
2) API Gateway - To setup api.
3) Serverless (Lambda):  -> LF0 -  performs the chat operation and interacts with Lex.
                         -> LF1 - A code hook for Lex. Also to manipulate and validate the parameters as well as format the bot's responses.
4) Lex - Has three intents -> Greeting Intent : Used for greeting user and provides reposne like "Hi there, how can I help?"
                           -> Thank You Intent : Thanks the user for using the service.
                           -> Dining Suggestion Intent : Collects information slots from user: Location, Cuisine, Dining Time, Number of People, Phone Number and Email.
5) SQS - To store user's request. It uses polling to fetch requests.
6) Elastic Search (Open Search) - To store restaurant ID and cuisine.
7) Dynamo DB - To store restaurants' information like: : Business ID, Name, Address, Coordinates, Number of Reviews, Rating & Zip Code
8) SNS - To send restaurant suggestions to users via SMS and Email. 

# FLOW:

<img src = "https://user-images.githubusercontent.com/26826339/190944214-83d40a95-abcd-486f-95d5-064b20608462.png"/>

<b>In summary</b>, based on a conversation with the customer, the LEX chatbot will identify the customer’s preferred ‘cuisine’. We will then search through ElasticSearch to get random suggestions of restaurant IDs with this cuisine. At this point, we would also need to query the DynamoDB table with these restaurant IDs to find more information about the restaurants we want to suggest to your customers like name and address of the restaurant. We are filtering restaurants only using the cuisine.
