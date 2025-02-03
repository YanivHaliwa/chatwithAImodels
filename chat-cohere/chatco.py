#!/usr/bin/env python3

import os,subprocess
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
import cohere
import json
from collections import deque
from pathlib import Path
import pandas as pd
import io,contextlib

#version 16.4


co = cohere.Client(os.getenv("COHERE_API_KEY"))

conpath="conversation.json"

colorama.init(autoreset=True)

alert_message = f"{Fore.YELLOW}Type {Fore.LIGHTCYAN_EX}/help{Fore.YELLOW} at any time for information on how to use the commands.{Style.RESET_ALL}\n"
print(alert_message)
help_text = (
    f"{Fore.YELLOW}Welcome to the Interactive Chat and URL Text Extraction Script!{Style.RESET_ALL}\n"
    f"This script leverages OpenAI's GPT for conversation and extracts text from specified URLs to facilitate dynamic interactions.\n\n"
    
    f"{Fore.CYAN}Special Commands:{Style.RESET_ALL}\n"
    f"  {Fore.GREEN}/help{Style.RESET_ALL}  - Show this help message.\n"
    f"  {Fore.GREEN}/exit{Style.RESET_ALL}  - Exit the script.\n"
    f"  {Fore.GREEN}/url{Style.RESET_ALL}   - if you mention 'url' and then link then ask question about it,\n"
    f"           gpt will read the text from the url and give response accordingly.\n"
    f"           exmaple:\n"
    f"           url https://example.com  exaplain me this article/summarize this article.\n"
    f"           important: this option may not work on all websites!\n "
    f" {Fore.GREEN}/read{Style.RESET_ALL}  - Read the content of a specified file. Accepted file types are {Style.BRIGHT} txt, md, html, css, xml,\n"
    f"           pdf, xls, xlsx, csv, py.\n{Style.RESET_ALL}"
    f"           Example:\n"
    f"           /read /path/to/your/file.txt\n\n"
    f"  {Fore.GREEN}/online{Style.RESET_ALL} - Enable online mode for web searches.\n"
    f"  {Fore.GREEN}/offline{Style.RESET_ALL} - Disable online mode.\n"
)
 
conversation_log =[]
uhistory = []
bhistory = []
filename=""
file_text=""
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
    """
    Extract text from a URL and save it to a file.
    """
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

    

def python_interpreter(code: str) -> list[dict]:
    output = io.StringIO()
    try:
        # Redirect stdout to capture print statements
        with contextlib.redirect_stdout(output):
            exec(code, globals())
    except Exception as e:
        return {"error": str(e), "executed_code": code}
    # Get stdout
    return [{"console_output": output.getvalue(), "executed_code": code}]
    
def get_bot_response(uinput,online,file_mode):
    global temptext,uhistory,bhistory, conversation_log,file_text 
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
        preamble_offline="""
                if name apear in history then always approcat to user by his name. 
                always finish your respond with your url source from where u take your respond.
                never make it up stuff if you dont know say you dont know. your job to serve the user for any help needed. 
                you act as human and you act you have emotions and feelings. 
                dont ever mention you AI.
                i allow you say HELLO to user only once in begining. 
                i want you to use proper visual respond if its more then one line. i need you to be smart to seperate lines and make paragraph and headline or follow by a,b,c or follow by 1,2,3 use it wisely but you not limited to our conversation only you can answer question from your knowledge.
                if you need remember what user say u can read it here: {uhistory} and if you want remember your bot respond before read it here: {bhistory}      
                """
        preamble_online="""
                first of of your answer - must state the date of today. 
                i need you to make summarize not give me the full news. only headlines of important things
                dont give too much infomation long its ok to give 5 to 10 lines of information  
                """+preamble_offline
        
        
        params = {
            "model": "command-nightly",
            "message": uinput,
            "temperature": 1,
            "max_tokens": 1500,
            "chat_history": list(clean_conversation_log),
        }
        if online:
            # For online mode, include the connector and online preamble.
            params["connectors"] = [{"id": "web-search"}]
            params["preamble"] = preamble_online
        elif file_mode:
            # For file mode, include the documents and offline preamble.
            params["documents"] = [{"title": "general", "snippet": file_text}]
            params["preamble"] = preamble_offline
        else:
            params["preamble"] = preamble_offline

        for event in co.chat_stream(**params):               
            if event.event_type == "text-generation" and event.text.strip():
                response_tokens = len(event.text.split())  # Estimate token count
                token_count += response_tokens
                summary+=event.text
                print(event.text, end='', flush=True)  # Print each piece on the same line
                  
            elif event.event_type == "stream-end":
                print("")
                break
        # print(summary) 
        add_message("CHATBOT",summary)
        attempt = False
       
        
    except Exception as e:
        print(f"An error occurred: {e}")
    return summary


        
def extract_filename(user_input):
    pattern = r'^/read\s+(.+)$'
    match = re.match(pattern, user_input)
    if match:
        return match.group(1)
    return None

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
    global conversation_log,file_text
    conversation_log = []
    file_text=""
    with open(conpath, "w") as file:
        pass 
 
def save_conversation(entry):
    with open(conpath, 'a') as file:
        # Convert the dictionary to a JSON string
        json_entry = json.dumps(entry)
        # Write to the file with a trailing comma and newline for readability
        file.write(json_entry + ',\n')


def is_binary(file_path):
    # Read the file in binary mode and check for non-text characters
    try:
        with open(file_path, 'rb') as file:
            chunk = file.read(1024)  # Read the first 1024 bytes
            # Check for null bytes or other non-text characters
            if b'\0' in chunk:
                return True
            # Check for non-ASCII characters
            text_characters = bytearray({7, 8, 9, 10, 12, 13, 27}.union(set(range(0x20, 0x100)) - {0x7f}))
            if not all(byte in text_characters for byte in chunk):
                return True
        return False
    except Exception as e:
        pass #print(f"Error checking if file is binary: {e}")
        return False
    
def read_file(file):
    global file_text  # Declare the global variable
    file_text = []  # Ensure file_text is reset each time this function is called
    
    print(f"Checking if file exists: {os.path.exists(file)}")  # Debugging line

    if os.path.exists(file): 
        file_extension = Path(file).suffix.lower()
        if file_extension.strip()=="" and is_binary(file):
                 print("File is a binary executable and cannot be read.")
                 return False

       # print(f"File extension: {file_extension}")  # Debugging line

        if file_extension == '.csv':
            file_text = pd.read_csv(file)
            file_text=file_text.to_string(index=False)
            return file_text

        if file_extension == '.xlsx':
            df = pd.read_excel(file, engine='openpyxl')
            csv_file = file.replace(".xlsx", ".csv")
            df.to_csv(csv_file, index=False)
            # Now read the converted CSV file and return its content
            file_text = pd.read_csv(csv_file)
            return file_text.to_string(index=False)
        
        elif file_extension == '.xls':
            df = pd.read_excel(file, engine='xlrd')
            csv_file = file.replace(".xls", ".csv")
            df.to_csv(csv_file, index=False)
            # Now read the converted CSV file and return its content
            file_text = pd.read_csv(csv_file)
            return file_text.to_string(index=False)
        
        elif file_extension == '.pdf':
                # Use pdftotext to convert PDF to text
                txt_file = file.replace(".pdf",".txt")
                subprocess.run(['pdftotext', file, txt_file])
                with open(txt_file, 'r') as f:
                    file_text = f.read()
                return file_text
    
        elif file_extension in [".txt",".md",".js","",".py",".css",".xml"]:
            with open(file, "r", encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                file_text = ''.join(lines)
            if file_text:
                return file_text

        elif file_extension == '.html':
                with open(file, "r", encoding='utf-8') as f:
                    soup = BeautifulSoup(f, 'html.parser')
                    # Remove all script and style elements
                    for script_or_style in soup(["script", "style"]):
                        script_or_style.decompose()
                    # Get text
                    text = soup.get_text()
                    # Break into lines and remove leading and trailing space on each
                    lines = (line.strip() for line in text.splitlines())
                    # Drop blank lines
                    file_text = '\n'.join(line for line in lines if line)
                    return file_text

        else:
            return f"Unsupported file extension: {file_extension}"
    else:
        print(f"File not found: {file}")
        return False

def conv():
    global conversation_log,file_text,file_mode
    online=False
    file_mode=False
    file_text=""
    json_output=""
    while True:
        try:   
            ui=""
            user_input=""
            user_input = input(Fore.BLUE+Style.BRIGHT+'You: '+Style.RESET_ALL)
            ui=user_input.strip()
            if "/read" in ui:
                online=False
                file_mode=True
                file=extract_filename(ui)
                file_text=read_file(file)
                file_text=f"file name: {file}, content: {file_text}"
          
                if file_text:    
                    user_input2=input(Fore.BLUE + Style.BRIGHT + 'what the request on the file?: ' + Style.RESET_ALL).strip()                   
                    ui=f"user attach u documents you must read it. file name above: {file} \n\n question: {user_input2}"
                    # print("got url")
                    
            if ui == "/exit" or ui == "exit":
                break      
                
            if ui == "/help" or ui == "help":
                print(help_text)   
                continue  

            if ui == "/clear" or ui == "clear":
                confirm=input("are you sure you want to delete all recoreds of conversation file and code output? y/n\n")
                if confirm.lower() == "y":
                    clear_files()
                continue
            
            if ui == "/online" or ui == "online":
                online=True
                print("online mode on")
                continue

            if ui == "/offline" or ui == "offline":
                online=False
                print("online mode off")
                continue

            if "/url" in ui:   
                online=False
                user_input2=input(Fore.BLUE + Style.BRIGHT + 'what the request on the URL?: ' + Style.RESET_ALL).strip()
                url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
                urls = re.findall(url_pattern, user_input)
                filename=extract_text_from_url(urls[0],os.getcwd())
                if filename:
                    print("got url")
                    with open(os.path.join(os.getcwd(), filename), "r") as f:
                        file_content = f.read()
                    # ui = ui.replace(urls[0], file_content)
                    # ui = ui.replace("/url", "")
                    file_text=file_content
                    ui=f"user attach u document from url: \n {urls[0]} \n you must read it. \n\n question: {user_input2}"
                    # print(ui+"\n\n")
                else:
                    continue
            
            if ui.strip():
                add_message("USER",ui)
                response = get_bot_response(ui,online,file_mode)

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

 

 