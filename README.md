# Foreing Language Sentence Creation Application

This python script pulls studied/learned cards from Anki foreign language vocabulary decks, compiles the words and asks ChatGPT for sentences of a specific level of grammatical difficulty in your native language. The intent is to practice translating to your foreign language with these generated sentences.

## Getting Started

### Dependencies

- Python 3.10.12 (or higher)
- Python packages as listed in the 'requirements.txt' file
  - Install the dependencies by running the following command:
    ```
    pip install -r requirements.txt
    ```
- Anki Desktop installed with the AnkiConnect plugin running.
- ChatGPT developer account with a valid API key.

### Installing

- Clone the repository to your local machine.
- Create a virtual env and install all required dependencies
  ```
  python3 -m venv new_dev_venv && source new_dev_venv/bin/activate && pip install -r requirements.txt
  ```
- Add a '.env' file to the root directory of the application and add the following information
  ```
  CHATGPT_API_KEY = "bolt://<Neo4J_DB_Address>:7687"
  ```

### Executing program

- Once you have everything setup, simply run the python script with `python3 generateSentences.py`
