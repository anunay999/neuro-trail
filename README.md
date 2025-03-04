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

## Demo
![Demo](https://neuro-trail.streamlit.app)

## Project Setup

### Initialize the Project with Docker

Run the following command to build and start the project:

```sh
docker compose up --build
```

It should start a streamlit app on port `8503`.

## Future Enhancements
- User memory persistence for personalized learning paths
- Agent Ecosystem for personalized experience
- Quiz Generation
- Multi-modal EPUB analysis (text, tables, images)
- Expanded document support (PDFs, DOCX)
- AI-driven feedback refinement

## Advanced settings
- Modify the environment variables in the docker-compose.yml file to customize neo4j project settings.
- To run Ollama, ensure it is installed and accessible from the Docker container. Update the environment variables in the docker-compose.yml file accordingly.

## Resources
- [Intro Blog](https://medium.com/@anunayaatipamula/building-a-memory-augmented-learning-companion-from-idea-to-implementation-49970ac6da16)

## Contribution
Feel free to fork, modify, and submit PRs to improve the project!

## License
Apache License 2.0
