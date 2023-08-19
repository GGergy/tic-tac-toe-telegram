import json


with open('assets/secure/config.json') as file:
    data = json.load(file)
    TOKEN = data['token']
