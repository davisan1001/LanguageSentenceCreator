import os
from dotenv import load_dotenv
import json
import requests
import openai

load_dotenv()

ANKI_URL = "http://localhost:8765"
CHATGPT_API_KEY = os.getenv('CHATGPT_API_KEY')

'''
findCards : Searches for cards based on a query
{
    "action": "findCards",
    "version": 6,
    "params": {
        "query": "deck:current"
    }
}

cardsInfo : Returns all the information from the card id's given
{
    "action": "cardsInfo",
    "version": 6,
    "params": {
        "cards": [1498938915662, 1502098034048]
    }
}
'''
def getAnki(request_data):
    response = requests.post(ANKI_URL, data=request_data)
    if response.status_code == 200:
        print(response.json())

def main():
    request = '''{
        "action": "findCards",
        "version": 6,
        "params": {
            "query": "deck:current"
        }
    }'''
    getAnki(request)
    return

if __name__ == "__main__":
    main()