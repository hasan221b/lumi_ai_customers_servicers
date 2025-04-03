# AI-Based cutomers services

## Overview
This project is anAI-Based cutomers services using **Retrieval-Augmented Generation (RAG)** designed to assist with eCommerce customer support. The chatbot processes FAQ-style data using FAISS for retrieval and generates responses using an embedding model and an LLM.

## Features
- **Fast & Accurate Retrieval**: Uses FAISS to index and retrieve relevant FAQ data.
- **Context-Aware Responses**: Combines retrieved knowledge with LLM-generated answers.
- **Sentiment Detection**: Analyze user sentiment (happy, frustrated) and adjust responses.
- **Proactive Recommendations**: Suggest related FAQs or actions based on the user’s query.
- **Multi-Turn Conversations**: Enable the chatbot to maintain context across multiple messages.
- **Query Refinement**: If the chatbot doesn’t fully understand a question, it can ask clarifying questions.
- **Modular Design**: Organized into multiple directories for better maintainability.
- **API Integration**: Built with FastAPI for serving chatbot responses.
- **Logging**: Logs are maintained for debugging and monitoring.
- **Frontend**: A simple UI for user interaction.

## Project Structure

```
lumi-chatbot-rag/
├── config/
│   └── config.yml
├── logs/
│   ├── app.log
│   └── pipeline.log
├── src/
│   ├── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── app.py  
│   ├── database/
│   │   ├── __init__.py
│   │   └── db.py 
│   ├── model/
│   │   ├── __init__.py
│   │   └── load_models.py
│   ├── processing/
│   │   ├── __init__.py
│   │   ├── data_embedder.py
│   │   ├── data_index.py
│   │   └── data_loader.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── logger.py
│   │   ├── setting.py
│   │   └── config.py
│   └── rag/
│       ├── __init__.py
│       ├── answer_generator.py  
│       └── retriever.py
├── data/
│   └── faqs.csv
├── frontend/
│   ├── index.html
│   ├── styles.css
│   ├── script.js  
│   └── assets/
│       └── bot-icon.png
└── chatbot.db
```

## Installation
### Prerequisites
- Python 3.9+
- FAISS (`faiss-cpu`)
- FastAPI
- Sentence Transformers (`sentence-transformers`)
- LnagChain

### Setup
1. Clone the repository:
   ```sh
   git clone https://github.com/your-repo/ecommerce-chatbot-rag.git
   cd ecommerce-chatbot-rag
   ```
2. Create a virtual environment:
   ```sh
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```

## Usage
### Running the API
Start the chatbot API with:
```sh
uvicorn src.api.app:app --reload
```
The API will be accessible at `http://127.0.0.1:8000`.

### Running the Frontend
Run this command:
```sh
python -m http.server 8000
```
Then open `http://127.0.0.1:8000` on your browser.

## Configuration
Modify `config/config.yml` to adjust model paths, API settings, and logging levels.

## Contributing
Feel free to contribute by submitting pull requests or reporting issues.
