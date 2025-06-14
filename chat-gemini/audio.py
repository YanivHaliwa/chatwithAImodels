import sys
import google.generativeai as genai
import os

genai.configure(api_key=os.environ["GEMINI_API_KEY"])

if len(sys.argv) != 2:
    print("Usage: python3 audio.py <file>")
    print("Example: python3 audio.py file.wav")
    sys.exit(1)

your_file = genai.upload_file(path=sys.argv[1])
prompt = "Listen carefully to the following audio file. Provide a brief summary."
model = genai.GenerativeModel('models/gemini-1.5-pro-latest')
response = model.generate_content([prompt, your_file])
print(response.text)
