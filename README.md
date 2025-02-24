# neuro-trail : Personalized & Memory-Augmented Learning Agent

## Overview
NeuroTrail is an AI-powered learning system designed to enhance personalized learning experiences by leveraging memory-augmented AI. The system allows users to upload and interact with knowledge sources (EPUBs, with future support for PDFs and DOCs), generate quizzes, track progress, and receive personalized learning digests.

### Key Features
- **Interactive Knowledge Upload**: Supports EPUB files for ingestion and interaction with an LLM.
- **Quiz Generation**: Uses embeddings and LLMs to generate self-testing questions from books.
- **Personalized Knowledge Trails**: Users can define learning paths based on interests.
- **Scheduled Learning Digests**: Periodic summaries sent via email.
- **Persistent Memory Module**: Tracks learned content and provides recommendations.
- **Deep Knowledge Graph Integration**: Ensures semantic linking and retrieval.

## Project Setup

### Prerequisites
- Install `uv` (Python package manager):
  ```sh
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```
- Ensure `pip` is up-to-date:
  ```sh
  uv pip install --upgrade pip
  ```

### Initialize the Project
```sh
uv venv .venv
source .venv/bin/activate  # Windows: `.venv\Scripts\activate`
uv init --name neuro-trail
```

### Install Dependencies
```sh
uv pip install -r requirements.txt
pip install faiss-cpu --no-cache-dir  # Use faiss-gpu if required
```

### Set Up Configuration
Edit `.env` and add:
```
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=passwoed
BOOK_PATH=/absolute/path/to/epub-folder
```

### Folder Structure
```
neuro_trail/
├── LICENSE               # Project license
├── README.md             # Documentation and setup guide
├── epub_extract.py       # Handles EPUB ingestion and processing
├── knowledge_graph.py    # Manages knowledge graph integration
├── learning_canvas.py    # Interactive learning canvas with LLM
├── llm.py                # LLM interaction and prompt handling
├── main.py               # Entry point for running the application
├── pyproject.toml        # Project configuration
├── requirements.txt      # List of dependencies
├── user_memory.py        # Persistent memory module for tracking learning
└── vector_store.py       # Manages vector embeddings for retrieval
```

### Running the Project
Specify the knowledge stack to process in `.env`, currently only supports epub
#### Start the Main Application
```sh
python main.py
```

## Future Enhancements
- Open UI integration
- Agent Ecosystem for personalized experience
- Quiz Generation
- Multi-modal EPUB analysis (text, tables, images)
- Historical and epistemic retrieval
- Expanded document support (PDFs, DOCX)
- AI-driven feedback refinement

## Contribution
Feel free to fork, modify, and submit PRs to improve the project!

## License
Apache License 2.0
