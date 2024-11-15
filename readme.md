
# AI Chatbot and Audio Analysis Scripts

This repository contains a collection of Python scripts for various AI-powered chatbots and audio analysis tools. Each script uses different AI models and APIs to provide unique functionalities.

## Scripts Overview

1. **chatcl.py** - Claude Chatbot
   - Uses Anthropic's Claude API
   - Features: URL text extraction, conversation history, artifact handling
   - Supports various file types for content analysis

2. **chatclpic.py** - Claude Chatbot with Image Support
   - Extension of chatcl.py with added image processing capabilities
   - Can handle both local image files and image URLs

3. **chatco.py** - Cohere Chatbot
   - Utilizes Cohere's AI model
   - Features: URL text extraction, file reading (including PDFs, Excel, CSV)
   - Supports online/offline modes for web search integration

4. **chatgo.py** - Google Gemini Chatbot
   - Implements a chatbot using Google's Generative AI (Gemini)
   - Features: URL text extraction, conversation history

5. **audio.py** - Audio Analysis with Google's Gemini AI
   - Uses Google's Gemini API for audio file analysis
   - Provides a brief summary of the audio content

6. **chat-hume.py** - Real-time Voice Analysis with Hume AI
   - Uses Hume's Voice API for real-time speech analysis
   - Features: Live transcription and emotion voice index (EVI) analysis

## Requirements

- Python 3.x
- Various Python libraries (see requirements.txt)
- API keys for Anthropic, Cohere, Google Gemini, and Hume AI

## Setup

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/ai-chatbot-scripts.git
   cd ai-chatbot-scripts
   ```

2. Install required packages:
   ```
   pip install -r requirements.txt
   ```

3. Set up environment variables for API keys:
   - ANTHROPIC_API_KEY
   - COHERE_API_KEY
   - GEMINI_API_KEY
   - HUME_API_KEY

## Usage

Run each script from the command line:

- Claude Chatbot: `python chatcl.py`
- Claude with Image: `python chatclpic.py <image_path>`
- Cohere Chatbot: `python chatco.py`
- Audio Analysis: `python audio.py <audio_file>`
- Google Gemini Chatbot: `python chatgo.py`
- Hume Voice Analysis: `python chat-hume.py`

Follow the on-screen prompts for each script. Use `/help` command in chat scripts for more information on available commands.

## Features

- Text-based chat interfaces
- Image and audio file analysis
- URL content extraction and analysis
- File reading and analysis (PDF, Excel, CSV, etc.)
- Real-time voice transcription and emotion analysis
- Conversation history management
- Online/offline modes (for web search integration)

## License

[MIT License](https://opensource.org/licenses/MIT)

## Acknowledgements

- [Anthropic](https://www.anthropic.com) for Claude AI
- [Cohere](https://cohere.ai) for their AI model
- [Google](https://ai.google.dev/) for Gemini AI
- [Hume AI](https://hume.ai) for voice analysis capabilities