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

HTML_CLEANR = re.compile('<.*?>|\&\S.*?\;') 

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
    cleantext = re.sub(HTML_CLEANR, '', raw)
    return cleantext

def cleanText(raw, remDigits=False):
    remDigitsPattern = re.compile('\d*')

    HTMLcleanedStr = cleanHTML(raw)
    if(remDigits):
        str = re.sub(remDigitsPattern, "", HTMLcleanedStr)
    else:
        str = HTMLcleanedStr

    return cleanHTML(str).strip()

# TODO: Make this use regex instead (maybe use re.match() ??)
def addWordPattern(str, pattern):
    return pattern.replace("<word>", str)

def removeWordPattern(str, pattern):
    return re.sub(pattern, "", str)

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

def compileCardFieldsList(cardsInfo, deckField, seperator, addPattern='<word>', remPattern='', splitByExistingSeperator=True):
    # TODO: Compile a list of all fields, cleaned and comma seperated.
    compiledCardFields = ""
    numCards = len(cardsInfo)

    for i in range(0, numCards):
        cleanedField = cleanText(cardsInfo[i]['fields'][deckField]['value'])

        # Split any existing comma seperated words in the field to process individually
        if (splitByExistingSeperator):
            splitField = cleanedField.split(', ')
            for j in range(0, len(splitField)):
                splitField[j] = cleanText(addWordPattern(removeWordPattern(splitField[j], remPattern), addPattern), remDigits=True)
            cleanedField = ', '.join(splitField)
        else:
            cleanedField = cleanText(addWordPattern(removeWordPattern(cleanedField, remPattern), addPattern), remDigits=True)

        compiledCardFields += cleanedField
        if (i < numCards-1):
            compiledCardFields += seperator
    return compiledCardFields

def main():
    deckName = INCLUDE_DECKS
    deckField = DECK_FIELDS
    seperator = ', ' # TODO: Temporary placeholder. Include this option elsewhere to allow user specification.
    # regex patterns... TODO: Make this user specifiable.
    addPattern = 'w:<word>' # TODO: Not regex right now, but make it regex!
    remPattern = re.compile('\(.*\)')
    print(deckName) # TODO: Debugging Purposes
    print(deckField) # TODO: Debugging Purposes

    cardIDs = getCardIDs(deckName)
    cardsInfo = getCardInfo(cardIDs)

    compiledCardFieldList = compileCardFieldsList(cardsInfo, deckField, seperator, addPattern, remPattern)
    print(compiledCardFieldList)

    return

if __name__ == "__main__":
    main()