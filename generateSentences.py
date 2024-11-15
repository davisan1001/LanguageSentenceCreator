import os
from dotenv import load_dotenv
import json
import requests
import re
import openai

load_dotenv(override=True)

ANKI_URL = os.getenv("ANKI_URL") # 'http://localhost:8765"
CHATGPT_API_KEY = os.getenv('CHATGPT_API_KEY')

INCLUDE_DECKS = os.getenv("INCLUDE_DECKS")
DECK_FIELDS = os.getenv("DECK_FIELDS")

CLEANR = re.compile('<.*?>|\&\S.*?\;') 

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

def cleanHTML(raw):
    cleantext = re.sub(CLEANR, '', raw)
    return cleantext

def cleanText(raw):
    return cleanHTML(raw).strip()

def getAnki(request_data):
    response = requests.post(ANKI_URL, data=request_data)
    if response.status_code == 200:
        response_json = json.loads(response.content)
        if response_json['error'] == None:
            return response_json['result']

def getCardIDs(deckName):
    request = {}
    params = {}
    request['action'] = 'findCards'
    request['version'] = 6
    params["query"] = '"deck:' + deckName + '"' + " -is:new"
    request['params'] = params
    json_request_data = json.dumps(request, indent=2, ensure_ascii=False)
    return getAnki(json_request_data)

def getCardInfo(cardIDs):
    request = {}
    params = {}
    params["cards"] = cardIDs
    request['action'] = 'cardsInfo'
    request['version'] = 6
    request['params'] = params
    json_request_data = json.dumps(request, indent=2, ensure_ascii=False)
    return getAnki(json_request_data)

def compileFieldList(cardsInfo, deckField):
    # TODO: Compile a list of all fields, cleaned and comma seperated.
    return

def main():
    deckName = INCLUDE_DECKS
    deckField = DECK_FIELDS
    print(deckName)
    print(deckField)

    cardIDs = getCardIDs(deckName)
    cardsInfo = getCardInfo(cardIDs)

    fieldList = compileFieldList(cardsInfo, deckField)
    print(fieldList)

    #print(cleanHTML(cardsInfo[0]['fields'][deckField]['value']))
    
    return

if __name__ == "__main__":
    main()