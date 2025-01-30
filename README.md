# Foreign Language Sentence Creation Application

This python script pulls studied/learned cards from Anki foreign language vocabulary decks, compiles the words and asks ChatGPT for sentences of a specific level of grammatical difficulty in your native language. The intent is to practice translating to your intended foreign language with these generated sentences.

## Getting Started

### Dependencies

- Python 3.10.12 (or higher)
- Python packages as listed in the 'requirements.txt' file
  - Install the dependencies by running the following command:
    ```
    pip install -r requirements.txt
    ```
- Anki Desktop installed with the AnkiConnect plugin running.
- ChatGPT developer account with a valid API key. (optional)
> **_NOTE:_**  An OpenAPI developer account and API key is not required. Simply run the program with the `-p` flag to output the prompt only, then you can copy and paste it into your LLM of choice.

### Installing

- Clone the repository to your local machine.
- Create a virtual env and install all required dependencies
  ```
  python3 -m venv my_venv && source my_venv/bin/activate && pip install -r requirements.txt
  ```
- Add a '.env' file to the root directory of the application and add the following information
  ```
  # ChatGPT API Key
  CHATGPT_API_KEY = <api_key>                                 # Leave this blank if not using.
  
  # Anki Connect Settings
  ANKI_URL = http://localhost:<AnkiConnect_port>
  
  INCLUDE_DECKS = <deck_1>;<deck_2>;<deck_3>                  # Example:  Korean::어휘::500 Words Book 1;Korean Vocabulary by Evita
  DECK_FIELDS = <deck_1_field>;<deck_2_field>;<deck_3_field>  # Example:  Korean;Korean
  
  # Prompt Settings
  NATIVE_LANGUAGE = <native_language>                         # Example:  English
  TARGET_LANGUAGE = <target_language>                         # Example:  Korean
  GRAMMATICAL_DIFFICULTY_LEVEL = <grammatical_difficulty>     # Example:  ADVANCED (can be e.g. EASY, MEDIUM, ADVANCED, VERY ADVANCED)
  ```

### Executing program

- Once you have everything setup, simply run the python script with `python3 generateSentences.py`
- Please view the help page with `python3 generateSentences.py -h` to view all available options.


## For the Developer

### Dumping pip Requirements

- Run `pip freeze > requirements.txt`
