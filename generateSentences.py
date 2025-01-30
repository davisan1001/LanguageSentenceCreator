import os
from dotenv import load_dotenv, dotenv_values
import argparse
import json
import requests
import re
import copy
from openai import OpenAI
import openai

## ~~~  Global Variables  ~~~ ##
parser = None
args = None
'''
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
'''
config = dotenv_values(".env")

if "OPENAI_API_KEY" in config: OPENAI_API_KEY = config["OPENAI_API_KEY"]
else: OPENAI_API_KEY = None
if "OPENAI_API_ORGANIZATION" in config: OPENAI_API_ORGANIZATION = config["OPENAI_API_ORGANIZATION"]
else: OPENAI_API_ORGANIZATION = None
if "ANKI_URL" in config: ANKI_URL = config["ANKI_URL"] # 'http://localhost:8765"
else: ANKI_URL = None

if "INCLUDE_DECKS" in config:
    INCLUDE_DECKS = config["INCLUDE_DECKS"].split(';')
    INCLUDE_DECKS = [val.strip() for val in INCLUDE_DECKS]
else:
    INCLUDE_DECKS = None
if "DECK_FIELDS" in config:
    DECK_FIELDS = config["DECK_FIELDS"].split(';')
    DECK_FIELDS = [val.strip() for val in DECK_FIELDS]
else:
    DECK_FIELDS = None

if "NATIVE_LANGUAGE" in config: NATIVE_LANGUAGE = config["NATIVE_LANGUAGE"]
else: NATIVE_LANGUAGE = None
if "TARGET_LANGUAGE" in config: TARGET_LANGUAGE = config["TARGET_LANGUAGE"]
else: TARGET_LANGUAGE = None
if "GRAMMATICAL_DIFFICULTY_LEVEL" in config: GRAMMATICAL_DIFFICULTY_LEVEL = config["GRAMMATICAL_DIFFICULTY_LEVEL"]
else: GRAMMATICAL_DIFFICULTY_LEVEL = None

HTML_CLEANR = re.compile(r'<.*?>|\&\S.*?\;')
DIGIT_CLEANR = re.compile(r'\d*')


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


## ~~~  AnkiConnect Functions  ~~~ ##

# Test the AnkiConnect Connection. Return 1 if successful, Return -1 if failed.
def testAnkiConnectConnection():
    if(ANKI_URL == None):
        print("Error: No AnkiConnect URL provided in dotenv.")
        return -1
    
    # Test connection.
    try:
        response = requests.options(ANKI_URL)
        if not response.ok:
            print(f"Error: AnkiConnect API is accessible, but an error occured. Response code : {response.status_code}")
            return -1
    except (requests.exceptions.HTTPError, requests.exceptions.ConnectionError) as e:
        print("Error: Could not reach AnkiConnect.\nMake sure the URL and port are correct and that Anki is open and running in the background.")
        return -1
    except Exception as e:
        print(f"Error: An unknown error occurred: {e}.")
        return -1
    
    return 1


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
def getCardIDs(deckName, queryParams):
    request = {}
    params = {}
    request['action'] = 'findCards'
    request['version'] = 6
    params["query"] = '"deck:' + deckName + '"' + queryParams
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

# Returns a 'separator' seperated list of words compiled from the 'deckField' of all cards in 'cardsInfo'. Fields extract are also cleaned.
def compileCardFields(cardsInfo, deckField, separator, addPattern, remPattern, existingSeparatorFilter, splitByExistingSeparator):
    compiledCardFields = ""
    numCards = len(cardsInfo)

    for i in range(0, numCards):
        cleanedField = cleanText(cardsInfo[i]['fields'][deckField]['value'])

        # Split any existing 'separator' seperated words in the field to process individually.
        if (splitByExistingSeparator):
            splitField = re.split(existingSeparatorFilter, cleanedField)
            for j in range(0, len(splitField)):
                splitField[j] = cleanText(addWordPattern(removeWordPattern(splitField[j], remPattern), addPattern), remDigits=True)
            cleanedField = separator.join(splitField)
        else:
            cleanedField = cleanText(addWordPattern(removeWordPattern(cleanedField, remPattern), addPattern), remDigits=True)

        compiledCardFields += cleanedField
        if (i < numCards-1):
            compiledCardFields += separator
    return compiledCardFields


## ~~~  LLM Functions  ~~~ ##

# Returns the full prompt for an LLM
def createLLMPrompt(masterWordList):
    global GRAMMATICAL_DIFFICULTY_LEVEL, NATIVE_LANGUAGE, TARGET_LANGUAGE

    prompt = "Create 30 sentences of [grammatical_difficulty_level] grammatical difficulty in [native_language] "
    prompt += "based ONLY on the list of words following this paragraph.\n"
    prompt += "DO NOT include words that are not included in the following list.\n"
    prompt += "The intention for these sentences is to be translated from [native_language] to [target_language], for practice.\n"
    prompt += "Along with the list of 50 sentences, please provide the native equivalent/translations in [target_language] for ALL "
    prompt += "of the sentences. Include these translations in a seperate list in the same order that they appear in the first list "
    prompt += "to be used as a reference/answer-key.\n\n"
    prompt += "Word List for Sentence Generation:\n" + masterWordList

    # Check if placeholders are specified in the dotenv. If not, ask the user for their values using the CLI.
    while(GRAMMATICAL_DIFFICULTY_LEVEL == None or GRAMMATICAL_DIFFICULTY_LEVEL.strip() == ""):
        print("No grammatical difficulty level specified...")
        GRAMMATICAL_DIFFICULTY_LEVEL = input("Please specify grammatical difficulty level: ")
    while(NATIVE_LANGUAGE == None or NATIVE_LANGUAGE.strip() == ""):
        print("No native language specified...")
        NATIVE_LANGUAGE = input("Please specify native language: ")
    while(TARGET_LANGUAGE == None or TARGET_LANGUAGE.strip() == ""):
        print("No target language specified...")
        TARGET_LANGUAGE = input("Please specify target language: ")
    
    # Replace placeholders
    prompt = prompt.replace("[grammatical_difficulty_level]", GRAMMATICAL_DIFFICULTY_LEVEL)
    prompt = prompt.replace("[native_language]", NATIVE_LANGUAGE)
    prompt = prompt.replace("[target_language]", TARGET_LANGUAGE)

    return prompt

# Sends the LLM prompt to ChatGPT
def sendChatGPTPrompt(prompt):
    client = OpenAI(
        api_key=OPENAI_API_KEY
    )

    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "developer", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ]
        )
    except openai.APIConnectionError as e:
        print("The server could not be reached")
        print(e.__cause__)  # an underlying Exception, likely raised within httpx.
        return -1
    except (openai.AuthenticationError, openai.PermissionDeniedError) as e:
        print("An authentication/permission error occured. Your API key may be invalid.")
        print(e.response)
        return -1
    except openai.RateLimitError as e:
        print("A RateLimitError code was received; You may be out of requests.")
        return -1
    except openai.APIStatusError as e:
        print("Another non-200-range status code was received")
        print(e.status_code)
        print(e.response)
        return -1

    return completion.choices[0].message


## ~~~  Additional Output Functions  ~~~ ##

# Outputs a given string to a file
def outputToFile(content, filename):
    file = open(filename, "w")
    file.write(content)
    file.close()
    return


## ~~~  MAIN  ~~~ ##
def setupArgParser():
    global parser, args

    parser = argparse.ArgumentParser(
                    formatter_class=argparse.RawDescriptionHelpFormatter,
                    prog='sentenceGenerator',
                    description='Generate sentences in your language of choice with a grammatical difficulty of choice, using a parsed list of words from Anki decks.',
                    epilog='''If no command line arguments are specified, the default behaviour is:
                    \r1. extract and compile all words from Anki decks specified in the dotenv, comma seperated, with parenthesized content removed, and with nothing added.
                    \r2. Compile an LLM prompt to construct sentences based on what is specified in the dotenv or gathered through the CLI
                    \r3. Send the prompt to ChatGPT via the OpenAI API, and
                    \r4. Print the response on the CLI.
                    ''')

    parser.add_argument('-ps', '--parseSeparator', nargs=1, help='Specify a custom separator for the word list gathered from Anki decks. Default if not specified = \', \'.')
    parser.add_argument('-pa', '--parseAddPattern', nargs=1, help='Specify a custom pattern to add to each word parsed from Anki. The string "<word>" in your specified pattern will be replaced with parsed anki word. Default if not specified = \'<word>\'.')
    parser.add_argument('-pr', '--parseRemPattern', nargs=1, help='Specify a custom regex to remove all matching parts from each word parsed from Anki. This is helpful is you need to remove things like parentheses. Default if not specified = \'\\(.*\\)\' --> removes everything in parentheses.')
    parser.add_argument('-se', '--splitExisting', nargs=1, help='Specify if you want existing separators in the anki card to be split and handled as separate words. Example: \',|;\' will separate existing commas or semicolons and process each word split individually.')
    parser.add_argument('-qp', '--queryParams', nargs=1, help='Specify a custom Anki query. Default if not specified = " -is:new" -> get\'s all cards that have already been seen/learned by the user.')
    parser.add_argument('-a', '--getAnkiParse', action='store_true', help='Output the parse of all words gathered from Anki decks only. Do not create prompt or send to ChatGPT.')
    parser.add_argument('-p', '--getPrompt', action='store_true', help='Output the LLM prompt only. Do not send prompt to chatGPT API.')
    parser.add_argument('-o', '--outputFile', nargs=1, help='Output to a file instead of the command line.')

    args = parser.parse_args()
    return

def main():
    # Setup argparse
    setupArgParser()


    # ERROR CHECKING: Make sure that at least one deckName exists to parse from Anki
    if(INCLUDE_DECKS == None):
        print("Error: No deck names are specified in dotenv... At least one is required... Exiting.")
        return -1
    if(DECK_FIELDS == None):
        print("Error: No deck fields are specified in dotenv... At least one is required... Exiting.")
        return -1
    
    deckNames = INCLUDE_DECKS
    deckFields = DECK_FIELDS
    
    # ERROR CHECKING: Make sure each deck to be included has a corresponding field to scrape.
    if(len(deckNames) != len(deckFields)):
        print("Error: Number of decks to include does not match number of fields...")
        return -1

    # Sets the separator of the returned word list
    if(args.parseSeparator):
        separator = args.parseSeparator[0]
    else:
        separator = ', '
    # Used to add a pattern of text to each word in the word list
    if(args.parseAddPattern):
        addPattern = args.parseAddPattern[0]
    else:
        addPattern = '<word>' # 'w:<word>' # TODO: Not regex right now, but make it regex!
    # Used to remove a regex pattern from each word returned in the Anki query
    if(args.parseRemPattern):
        remPattern = re.compile(args.parseRemPattern[0])
    else:
        remPattern = re.compile(r'\(.*\)') # Default removes anything in brackets ()

    if(args.splitExisting != None):
        splitByExistingSeparator = True
        existingSeparatorFilter = args.splitExisting[0]
    else:
        splitByExistingSeparator = False
        existingSeparatorFilter = ''

    if(args.queryParams != None):
        queryParams = args.queryParams[0]
    else:
        queryParams = " -is:new"

    # Test connection to AnkiConnect is open and ready. If not, provide a detailed error and exit.
    if(testAnkiConnectConnection() < 0):
        return -1

    # Build the entire word list from all specified Anki decks
    masterWordList = ""
    
    for i in range(0, len(deckNames)):
        cardIDs = getCardIDs(deckNames[i], queryParams)
        cardsInfo = getCardInfo(cardIDs)
        compiledWordList = compileCardFields(cardsInfo, deckFields[i], separator, addPattern, remPattern, existingSeparatorFilter, splitByExistingSeparator)

        masterWordList += compiledWordList

    # Variable to hold output text.
    finalOutput = ""

    if(args.getAnkiParse):
        finalOutput = masterWordList
    else:
        prompt = createLLMPrompt(masterWordList)
        if(args.getPrompt):
            finalOutput = prompt
        else:
            # Make sure ChatGPT API key exists. Else, revert to prompt only output.
            if(OPENAI_API_KEY == None):
                print("Error: No ChatGPT API Key specified in dotenv... Returning prompt only.")
                finalOutput = prompt
            else:
                finalOutput = sendChatGPTPrompt(prompt)
                if finalOutput == -1: return -1

    # Output the final compiled output to CLI or File
    if(args.outputFile != None):
        outputToFile(finalOutput, args.outputFile[0])
    else:
        print(finalOutput)
    
    return 1

if __name__ == "__main__":
    main()