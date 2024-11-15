#!/usr/bin/env python3

import os
import textwrap
import colorama
from colorama import Fore, Style
from urllib.parse import urlparse
import re
import requests
import time
import threading
import sys
import time
from datetime import datetime, timedelta
from requests.exceptions import HTTPError, ConnectionError, Timeout, RequestException
from bs4 import BeautifulSoup
from datetime import datetime
import json
from collections import deque
import google.generativeai as genai

genai.configure(api_key=os.environ["GEMINI_API_KEY"])

conpath="conversation.json"

colorama.init(autoreset=True)
alert_message = f"{Fore.YELLOW}Type {Fore.LIGHTCYAN_EX}/help{Fore.YELLOW} at any time for information on how to use the commands.{Style.RESET_ALL}\n"
print(alert_message)

help_text = (
    f"{Fore.YELLOW}Welcome to the Interactive Chat and URL Text Extraction Script!{Style.RESET_ALL}\n"
    f"This script leverages OpenAI's GPT for conversation and extracts text from specified URLs to facilitate dynamic interactions.\n\n"
    
    f"{Fore.CYAN}Special Commands:{Style.RESET_ALL}\n"
    f"  {Fore.GREEN}/help{Style.RESET_ALL} - Show this help message.\n"
    f"  {Fore.GREEN}exit{Style.RESET_ALL}  - Exit the script.\n"
    f"  {Fore.GREEN}url{Style.RESET_ALL}   - if you mention 'url' and then link then ask question about it,\n"
    f"          gpt will read the text from the url and give response accordingly.\n"
    f"          exmaple:\n"
    f"          url https://example.com  exaplain me this article/summarize this article.\n\n"
    f"          important: this option may not work on all websites! "
)
 
conversation_log =[]
uhistory = []
bhistory = []
filename=""
CHUNK_SIZE = 1024  

timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def process_conversation_log(conversation_log):
    # Initialize lists to hold user and chatbot history
    uhistory = []
    bhistory = []

    # Iterate through each entry in the conversation log
    for entry in conversation_log:
        # Check the role and append the message to the corresponding history list
        if entry['role'] == 'USER':
            uhistory.append(entry['message'].strip())
        elif entry['role'] == 'CHATBOT':
            bhistory.append(entry['message'].strip())

    # Return the separate lists for user history and chatbot history
    return uhistory, bhistory
 
 
def extract_text_from_url(url, output_dir):
    try:
        response = requests.get(url, timeout=10)  # Added timeout for the request
        response.raise_for_status()  # This will raise an HTTPError for bad responses

        response = requests.get(url)

        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        for script in soup(["script", "style"]):
            script.decompose()

        text = soup.get_text()

        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)

        title = soup.title.string if soup.title else "default_title"  # use "default_title" if title is None
        title = re.sub(r'[\W_]+', '_', title)

        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        filename = f"{title}_{timestamp}.txt"

        with open(os.path.join(output_dir, filename), 'w') as f:
            f.write(text)
        return filename

    except HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}") 
    except ConnectionError:
        print("Error connecting to the server. Please check your internet connection or the website may be down.")
    except Timeout:
        print("The request timed out. Please try again later.")
    except RequestException as err:
        print(f"An unexpected error occurred: {err}")
    except Exception as e:
        print(f"An error occurred: {e}")

    return None

    

def get_bot_response(uinput):
    global temptext,uhistory,bhistory, conversation_log  
    temptext=""
    summary=""
    attempt = True
    conversation_temp=""
    last_user_index = None
    token_count = 0
    for i, line in enumerate(reversed(conversation_log)):
        if "USER:" in line:
            last_user_index = len(conversation_log) - i - 1
            break

    if last_user_index is not None:
        conversation_temp = conversation_log[:last_user_index]
    clean_conversation_log = validate_and_clean_log(conversation_log)
    try:
        generation_config = {
            "temperature": 1,
            "top_p": 0.95,
            "top_k": 64,
            "max_output_tokens": 8192,
            "response_mime_type": "text/plain",
            }
        safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_NONE",
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_NONE",
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_NONE",
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_NONE",
            },
            ]
        model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        safety_settings=safety_settings,
        generation_config=generation_config,
        )

        chat_session = model.start_chat(
        history=[
        ]
        )
        
        response = chat_session.send_message(uinput)
        summary=response.text

        add_message("CHATBOT",summary)
        
        print(summary, end='', flush=True) 
        attempt = False
    except Exception as e:
        print(f"An error occurred: {e}")
     

    return summary


def validate_and_clean_log(conversation_log):
    cleaned_log = []
    for entry in conversation_log:
        # Check if 'message' key exists and is not empty
        if 'message' in entry and entry['message'].strip():
            cleaned_log.append(entry)
    return cleaned_log


def read_history(filename=conpath, max_lines=20):
    global conversation_log
    conversation_log = deque(maxlen=max_lines)
    if os.path.exists(filename):
        with open(filename, 'r') as file:
            for line in file:
                if line.strip().endswith(','):
                    line = line.strip()[:-1]
                try:
                    parsed_line = json.loads(line)
                    if parsed_line['message']:  # Ensure there's a message
                        conversation_log.append(parsed_line)
                except json.JSONDecodeError as e:
                    pass  # Handle or log errors as needed
    return list(conversation_log)
 
 
def clear_files():
    conversation_log = []
    with open(conpath, "w") as file:
        pass 
 
def save_conversation(entry):
    with open(conpath, 'a') as file:
        # Convert the dictionary to a JSON string
        json_entry = json.dumps(entry)
        # Write to the file with a trailing comma and newline for readability
        file.write(json_entry + ',\n')



def conv():
    global conversation_log
    json_output=""
    while True:
        try:   
            ui=""
            user_input=""
            user_input = input(Fore.BLUE+Style.BRIGHT+'You: '+Style.RESET_ALL)
            ui=user_input.lower()

            if ui == "exit":
                break      
                
            if ui == "/help":
                print(help_text)   
                continue  

            if ui == "/clear":
                confirm=input("are you sure you want to delete all recoreds of conversation file and code output? y/n\n")
                if confirm.lower() == "y":
                    clear_files()
                continue

            if "url" in ui:        
                url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
                urls = re.findall(url_pattern, user_input)
                filename=extract_text_from_url(urls[0],os.getcwd())
                if filename:
                    print("got url")
                    with open(os.path.join(os.getcwd(), filename), "r") as f:
                        file_content = f.read()
                    ui = ui.replace(urls[0], file_content)
                    ui = ui.replace("url", "")
                    print(ui+"\n\n")
                else:
                    continue
            
            if ui.strip():
                add_message("USER",ui)
            # save_conversation(texttoadd)
                response = get_bot_response(ui)
            

        except KeyboardInterrupt:
            print("\n")   
            try:
                inp = input(Fore.BLUE + Style.BRIGHT + 'You want to exit? (y/n): ' + Style.RESET_ALL).strip()
                if inp.lower() == "y":
                    print("Exiting...")
                    break  
                else:
                    print("Resuming...")   
            except KeyboardInterrupt:
                print("\nMultiple interrupt signals received. Exiting...")
                break   
 

def add_message(role, message):
    if message.strip(): 
        conversation_log.append({"role": role, "message": message})
        save_conversation({"role": role, "message": message})


read_history()
uhistory, bhistory = process_conversation_log(conversation_log)
conv()

 

 