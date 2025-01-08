import os
from dotenv import load_dotenv
import json
import requests
import re
import openai

load_dotenv(override=True)

CHATGPT_API_KEY = os.getenv('CHATGPT_API_KEY')
ANKI_URL = os.getenv("ANKI_URL") # 'http://localhost:8765"

INCLUDE_DECKS = os.getenv("INCLUDE_DECKS").split(';')
INCLUDE_DECKS = [val.strip() for val in INCLUDE_DECKS]
DECK_FIELDS = os.getenv("DECK_FIELDS").split(';')
DECK_FIELDS = [val.strip() for val in DECK_FIELDS]

NATIVE_LANGUAGE = os.getenv("NATIVE_LANGUAGE")
TARGET_LANGUAGE = os.getenv("TARGET_LANGUAGE")
GRAMMATICAL_DIFFICULTY_LEVEL = os.getenv("GRAMMATICAL_DIFFICULTY_LEVEL")

HTML_CLEANR = re.compile('<.*?>|\&\S.*?\;')
DIGIT_CLEANR = re.compile('\d*')

# Examples
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
## ~~~  Text Cleaning Functions  ~~~ ##

def cleanText(raw, remDigits=False):
    # Clean any HTML in the text
    cleanedStr = re.sub(HTML_CLEANR, '', raw)

    # Clean any digits from the text (only if remDigits==True)
    if(remDigits):
        str = re.sub(DIGIT_CLEANR, "", cleanedStr)
    else:
        str = cleanedStr

    return str.strip()

# TODO: Make this use regex instead (maybe use re.match() ??)
def addWordPattern(str, pattern):
    return pattern.replace("<word>", str)

def removeWordPattern(str, pattern):
    return re.sub(pattern, "", str)


## ~~~  AnkiConnect Field Extraction Functions  ~~~ ##

# Returns the response section of returned data from AnkiConnect.
#   Returns "ERROR" if an error occured.
def getAnki(request_data):
    response = requests.post(ANKI_URL, data=request_data)
    if response.status_code == 200:
        response_json = json.loads(response.content)
        if response_json['error'] == None:
            return response_json['result']
        else:
            return "ERROR"
    else:
        return "ERROR"

# Returns a list of Anki Card IDs in the deck
def getCardIDs(deckName):
    request = {}
    params = {}
    request['action'] = 'findCards'
    request['version'] = 6
    params["query"] = '"deck:' + deckName + '"' + " -is:new -is:suspended" # TODO: Make query parameters modifiable
    request['params'] = params
    json_request_data = json.dumps(request, indent=2, ensure_ascii=False)
    return getAnki(json_request_data)

# Returns a list of Anki Card details from a list of Card IDs
def getCardInfo(cardIDs):
    request = {}
    params = {}
    params["cards"] = cardIDs
    request['action'] = 'cardsInfo'
    request['version'] = 6
    request['params'] = params
    json_request_data = json.dumps(request, indent=2, ensure_ascii=False)
    return getAnki(json_request_data)

# Returns a 'seperator' seperated list of words compiled from the 'deckField' of all cards in 'cardsInfo'. Fields extract are also cleaned.
def compileCardFields(cardsInfo, deckField, seperator=', ', addPattern='<word>', remPattern='', existingSeperatorFilter=',|;', splitByExistingSeperator=False):
    # TODO: Compile a list of all fields, cleaned and comma seperated.
    compiledCardFields = ""
    numCards = len(cardsInfo)

    for i in range(0, numCards):
        cleanedField = cleanText(cardsInfo[i]['fields'][deckField]['value'])

        # Split any existing 'seperator' seperated words in the field to process individually.
        if (splitByExistingSeperator):
            splitField = re.split(existingSeperatorFilter, cleanedField)
            for j in range(0, len(splitField)):
                splitField[j] = cleanText(addWordPattern(removeWordPattern(splitField[j], remPattern), addPattern), remDigits=True)
            cleanedField = seperator.join(splitField)
        else:
            cleanedField = cleanText(addWordPattern(removeWordPattern(cleanedField, remPattern), addPattern), remDigits=True)

        compiledCardFields += cleanedField
        if (i < numCards-1):
            compiledCardFields += seperator
    return compiledCardFields


## ~~~  LLM Functions  ~~~ ##

# Returns the full prompt for an LLM
def createLLMPrompt(masterWordList): # TODO
    prompt = "Create 30 sentences of [grammatical_difficulty_level] grammatical difficulty in [native_language] "
    prompt += "based ONLY on the list of words following this paragraph.\n"
    prompt += "DO NOT include words that are not included in the following list.\n"
    prompt += "The intention for these sentences is to be translated from [native_langauge] to [target_language], for practice.\n"
    prompt += "Along with the list of 50 sentences, please provide the native equivalent/translations in [target_language] for ALL "
    prompt += "of the sentences. Include these translations in a seperate list in the same order that they appear in the first list "
    prompt += "to be used as a reference/answer-key.\n\n"
    prompt += "Word List for Sentence Generation:\n" + masterWordList


    # Replace placeholders
    prompt = prompt.replace("[grammatical_difficulty_level]", GRAMMATICAL_DIFFICULTY_LEVEL)
    prompt = prompt.replace("[native_language]", NATIVE_LANGUAGE)
    prompt = prompt.replace("[target_language]", TARGET_LANGUAGE)

    return prompt

# Sends the LLM prompt to ChatGPT
def sendChatGPTPrompt(prompt): # TODO
    return None


## ~~~  Additional Output Functions  ~~~ ##

# Outputs the word list to a file called 'Output.txt'
def outputWordListtoFile(masterWordList): # TODO
    return None


## ~~~  MAIN  ~~~ ##
def main():
    deckNames = INCLUDE_DECKS
    deckFields = DECK_FIELDS

    # ERROR CHECKING: Make sure each deck to be included has a corresponding field to scrape.
    if len(deckNames) != len(deckFields):
        print("Error: Number of decks to include does not match number of fields...")
        return -1

    # TODO: Make all of this user specifiable.
    # Sets the seperator of the returned word list
    seperator = ', ' # TODO: Temporary placeholder. Include this option elsewhere to allow user specification.
    # Used to add a pattern of text to each word in the word list
    addPattern = '<word>' # 'w:<word>' # TODO: Not regex right now, but make it regex!
    # Used to remove a regex pattern from each word returned in the Anki query
    remPattern = re.compile('\(.*\)')

    masterWordList = ""

    for i in range(0, len(deckNames)):
        cardIDs = getCardIDs(deckNames[i])
        cardsInfo = getCardInfo(cardIDs)
        compiledWordList = compileCardFields(cardsInfo, deckFields[i], seperator, addPattern, remPattern)

        masterWordList += compiledWordList

    prompt = createLLMPrompt(masterWordList)

    return

if __name__ == "__main__":
    main()