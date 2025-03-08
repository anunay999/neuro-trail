from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
import logging
from contextlib import asynccontextmanager

from app.api.v1.router import api_router
from app.core.config import settings
from app.db.session import engine, SessionLocal
from app.db.base_class import Base

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Update in lifespan function
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create tables, initialize connections
    logger.info("Starting up Neuro Trail API")
    Base.metadata.create_all(bind=engine)
    
    # Initialize plugin system
    from app.services.plugin_manager import plugin_manager
    logger.info("Discovering plugins...")
    plugin_manager.discover_plugins()
    
    # Initialize default plugins
    try:
        logger.info("Initializing default plugins...")
        await plugin_manager.initialize_plugin("vector_store", "chroma")
        await plugin_manager.initialize_plugin("llm", "ollama")
        await plugin_manager.initialize_plugin("embedding", "ollama")
        await plugin_manager.initialize_plugin("knowledge_graph", "neo4j")
        logger.info("Default plugins initialized successfully")
    except Exception as e:
        logger.warning(f"Error initializing some plugins: {e}")
    
    yield
    
    # Shutdown plugins
    logger.info("Shutting down plugins...")
    await plugin_manager.shutdown_all()
    
    # Shutdown: Close connections
    logger.info("Shutting down Neuro Trail API")


# Initialize FastAPI app
app = FastAPI(
    title="Neuro Trail API",
    description="Personalized Memory Augmented Learning API",
    version="0.1.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix="/api")


# Basic health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)