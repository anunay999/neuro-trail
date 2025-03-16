import logging

from smolagents import CodeAgent, HfApiModel, LiteLLMModel, load_tool

from v2.core.settings_config import settings
from v2.retriever.base import RetrieverTool
from v2.ui import GradioUI

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s-%(name)s-%(levelname)s-%(message)s"
)
logger = logging.getLogger(__name__)

# Import tool from Hub
# image_generation_tool = load_tool("m-ric/text-to-image", trust_remote_code=True)
retriever_tool = RetrieverTool()

model = LiteLLMModel(
    # model_id="ollama_chat/deepseek-r1:1.5b",  # This model is a bit weak for agentic behaviours though
    # model_id="ollama_chat/llama3.2",  # This model is a bit weak for agentic behaviours though
    model_id="ollama_chat/granite3.1-dense",  # This model is a bit weak for agentic behaviours though
    api_base="http://localhost:11434",  # replace with 127.0.0.1:11434 or remote open-ai compatible server if necessary
    api_key="YOUR_API_KEY",  # replace with API key if necessary
    num_ctx=8192,  # ollama default is 2048 which will fail horribly. 8192 works for easy tasks, more is better. Check https://huggingface.co/spaces/NyxKrage/LLM-Model-VRAM-Calculator to calculate how much VRAM this will need for the selected model.
)


# Initialize the agent with the image generation tool
agent = CodeAgent(tools=[retriever_tool], model=model)

GradioUI(
    agent, file_upload_folder=settings.persistant_storage_base / "uploads"
).launch()


# # Test retriever
# from v2.retriever.base import RetrieverTool
# retriever = RetrieverTool()
# retriever.forward(query="Rust")
