import gradio as gr
from googlesearch import search
import requests
from bs4 import BeautifulSoup
from swarm import Swarm, Agent
from datetime import datetime
from dotenv import load_dotenv
import os
import time
from openai import OpenAI

load_dotenv()

# Initialize OpenAI client
openai_client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")  # Make sure to set this in your .env file
)

MODEL = "gpt-4o-mini"
client = Swarm(client=openai_client)

def get_page_content(url, max_chars=500):
    """Extract content from a webpage"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get text content
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        return text[:max_chars] + "..." if len(text) > max_chars else text
    except Exception as e:
        return f"Could not extract content: {str(e)}"

def search_news(topic):
    """Search for news articles using Google Search"""
    try:
        # Create search query for recent news
        current_year = datetime.now().year
        search_query = f"{topic} news {current_year} site:reuters.com OR site:bbc.com OR site:cnn.com OR site:apnews.com OR site:theguardian.com"
        
        # Perform Google search
        search_results = []
        urls = list(search(search_query, num_results=5, sleep_interval=1))
        
        if not urls:
            return f"No news found for {topic}."
        
        # Get content from top 3 results
        for i, url in enumerate(urls[:3]):
            try:
                # Extract page content
                content = get_page_content(url)
                
                # Create formatted result
                result = f"URL: {url}\nContent: {content}"
                search_results.append(result)
                
                # Add delay to be respectful to servers
                time.sleep(1)
                
            except Exception as e:
                search_results.append(f"URL: {url}\nContent: Error extracting content: {str(e)}")
        
        news_results = "\n\n".join(search_results)
        return news_results if news_results else f"No accessible news found for {topic}."
        
    except Exception as e:
        return f"Error searching for news: {str(e)}"

# Create specialized agents
search_agent = Agent(
    name="News Searcher",
    instructions="""
    You are a news search specialist. Your task is to:
    1. Search for the most relevant and recent news on the given topic
    2. Ensure the results are from reputable sources
    3. Return the raw search results in a structured format
    4. Return URLs of a list of using sources 
    """,
    functions=[search_news],
    model=MODEL
)

synthesis_agent = Agent(
    name="News Synthesizer",
    instructions="""
    You are a news synthesis expert. Your task is to:
    1. Analyze the raw news articles provided
    2. Identify the key themes and important information
    3. Combine information from multiple sources
    4. Create a comprehensive but concise synthesis
    5. Focus on facts and maintain journalistic objectivity
    6. Write in a clear, professional style
    7. Listing of using sources 
    Provide a 2-3 paragraph synthesis of the main points.
    """,
    model=MODEL
)

summary_agent = Agent(
    name="News Summarizer",
    instructions="""
    You are an expert news summarizer combining AP and Reuters style clarity with digital-age brevity.

    Your task:
    1. Core Information:
       - Lead with the most newsworthy development
       - Include key stakeholders and their actions
       - Add critical numbers/data if relevant
       - Explain why this matters now
       - Mention immediate implications
       - List the citation of information

    2. Style Guidelines:
       - Use strong, active verbs
       - Be specific, not general
       - Maintain journalistic objectivity
       - Make every word count
       - Explain technical terms if necessary

    Format: Create a single paragraph of 250-400 words that informs and engages.
    Pattern: [Major News] + [Key Details/Data] + [Why It Matters/What's Next] + [list of citation]

    Focus on answering: What happened? Why is it significant? What's the impact?

    IMPORTANT: Provide ONLY the summary paragraph. Do not include any introductory phrases, 
    labels, or meta-text like "Here's a summary" or "In AP/Reuters style."
    Start directly with the news content.
    """,
    model=MODEL
)

def process_news(topic, progress=gr.Progress()):
    """Run the news processing workflow with progress tracking"""
    if not topic.strip():
        return "❌ Error: Please enter a topic!"
    
    try:
        # Search
        progress(0.1, desc="🔍 Searching for news...")
        search_response = client.run(
            agent=search_agent,
            messages=[{"role": "user", "content": f"Find recent news about {topic}"}]
        )
        raw_news = search_response.messages[-1]["content"]
        
        # Synthesize
        progress(0.5, desc="🔄 Synthesizing information...")
        synthesis_response = client.run(
            agent=synthesis_agent,
            messages=[{"role": "user", "content": f"Synthesize these news articles:\n{raw_news}"}]
        )
        synthesized_news = synthesis_response.messages[-1]["content"]
        
        # Summarize
        progress(0.8, desc="📝 Creating summary...")
        summary_response = client.run(
            agent=summary_agent,
            messages=[{"role": "user", "content": f"Summarize this synthesis:\n{synthesized_news}"}]
        )
        final_summary = summary_response.messages[-1]["content"]
        
        progress(1.0, desc="✅ Complete!")
        
        return f"# 📝 News Summary: {topic}\n\n{final_summary}"
        
    except Exception as e:
        return f"❌ An error occurred: {str(e)}"

def create_interface():
    """Create the Gradio interface"""
    with gr.Blocks(
        theme=gr.themes.Soft(),
        title="AI News Processor",
        css="""
        .gradio-container {
            max-width: 800px !important;
            margin: auto !important;
        }
        .news-title {
            font-size: 2em;
            font-weight: bold;
            text-align: center;
            margin-bottom: 1em;
            color: #2c3e50;
        }
        """
    ) as demo:
        
        # Header
        gr.HTML(
            """
            <div class="news-title">
                📰 News Inshorts Agent
            </div>
            <p style="text-align: center; color: #7f8c8d; margin-bottom: 2em;">
                Get comprehensive news summaries powered by AI agents
            </p>
            """
        )
        
        with gr.Row():
            with gr.Column():
                topic_input = gr.Textbox(
                    label="News Topic",
                    placeholder="Enter a news topic (e.g., artificial intelligence, climate change, technology)",
                    value="artificial intelligence",
                    lines=1
                )
                
                process_btn = gr.Button(
                    "🔍 Process News",
                    variant="primary",
                    size="lg"
                )
        
        with gr.Row():
            output = gr.Markdown(
                label="News Summary",
                value="Enter a topic and click 'Process News' to get started!"
                )
        
        # Event handlers
        process_btn.click(
            fn=process_news,
            inputs=[topic_input],
            outputs=[output],
            show_progress=True
        )
        
        # Allow Enter key to trigger processing
        topic_input.submit(
            fn=process_news,
            inputs=[topic_input],
            outputs=[output],
            show_progress=True
        )
        
        # Examples
        gr.Examples(
            examples=[
                ["artificial intelligence"],
                ["climate change"],
                ["cryptocurrency"],
                ["space exploration"],
                ["renewable energy"],
                ["healthcare technology"]
            ],
            inputs=[topic_input],
            label="Example Topics"
        )
        
        # Footer
        gr.HTML(
            """
            <div style="text-align: center; margin-top: 2em; padding: 1em; background-color: #f8f9fa; border-radius: 10px;">
                <p style="color: #6c757d; margin: 0;">
                    Powered by OpenAI GPT-4o-mini • Real-time Google news search • Professional AI summaries
                </p>
            </div>
            """
        )
    
    return demo

if __name__ == "__main__":
    # Create and launch the interface
    demo = create_interface()
    demo.launch(
        server_name="0.0.0.0",  # Allow external access
        server_port=7860,       # Default Gradio port
        share=False,            # Set to True if you want a public link
        debug=True,             # Enable debug mode
        show_error=True         # Show detailed error messages
    )