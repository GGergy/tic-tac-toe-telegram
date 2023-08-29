import json
import os

token = input('Enter token of your bot (will saved at source/assets/secure/config.json): ')


os.mkdir('source/assets/')
os.mkdir('source/assets/secure')

with open('source/assets/secure/config.json', mode='w') as file:
    json.dump({"token": token}, file)
os.system('pip install -r requirements')

print('Done! Now, you can start main.py and use your bot')
