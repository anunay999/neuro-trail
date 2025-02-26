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
- **Ensure the required EPUB files are placed in the books folder before building the Docker image.** 
- default Ollama model is deepseek-r1:1.5b. To use a different model, update the environment variables in the docker-compose.yml file accordingly.

### Initialize the Project with Docker

Run the following command to build and start the project:

```sh
docker-compose up --build
```
### Interact with the Application
Currently, the app runs in the terminal (UI integration is in progress). Once the Docker setup is complete, access the application by running:

```sh
docker-compose run python_app bash
```

Once inside the container, start the app with:

```sh 
uv run main.py
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
