# AI_Search_News

AI_Search_News is a simple demo that uses Gradio and OpenAI's Swarm framework to search for recent news and produce a short summary. After entering a topic, the application looks up news articles from several major sources, combines the information, and returns a concise overview.

## Installation

1. Use Python 3.9–3.11.
2. Install the dependencies:
   ```bash
   pip install -r requirement.txt
   ```
3. Create a `.env` file in the project root with your OpenAI API key:
   ```
   OPENAI_API_KEY=your_openai_key
   ```

## Running the app

Once dependencies are installed and the `.env` file is set up, start the interface with:

```bash
python ai_search_news.py
```

Gradio will launch at [http://localhost:7860](http://localhost:7860). Open this address in your browser, enter a topic, and you will receive a summarized version of the latest news.

## Features

- **Search** – queries Google for recent articles from sources like Reuters, BBC, CNN and others.
- **Synthesis** – extracts key details from multiple articles and combines them.
- **Summary** – generates a short, single-paragraph overview with citations.

This repository is intended as a reference implementation. Feel free to adapt or expand it to your needs.
