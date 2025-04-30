from common.server import A2AServer
from common.types import AgentCard, AgentCapabilities, AgentSkill, MissingAPIKeyError
from task_manager import AgentTaskManager
from agent import MarketAgent
import click
import os
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@click.command()
@click.option("--host", default="localhost")
@click.option("--port", default=10003)  # Changed to 10003 to avoid conflicts with your other agent
def main(host, port):
    try:
        # Check for API key only if Vertex AI is not configured
        if not os.getenv("GOOGLE_GENAI_USE_VERTEXAI") == "TRUE":
            if not os.getenv("GOOGLE_API_KEY"):
                raise MissingAPIKeyError(
                    "GOOGLE_API_KEY environment variable not set and GOOGLE_GENAI_USE_VERTEXAI is not TRUE."
                )
        
        capabilities = AgentCapabilities(streaming=True)
        skill = AgentSkill(
            id="market_discovery",
            name="Market Discovery Tool",
            description="Helps discover businesses within markets based on various criteria such as roles.",
            tags=["market", "business", "discovery"],
            examples=[
                "What markets are available?",
                "What businesses are in the Electronics Marketplace?",
                "Find sellers in the Electronics Marketplace",
                "What roles are supported in the Electronics Marketplace?",
                "Tell me about DeviceMart"
            ],
        )
        agent_card = AgentCard(
            name="Market Agent",
            description="This agent provides information about markets and helps discover businesses within markets based on various criteria.",
            url=f"http://{host}:{port}/",
            version="1.0.0",
            defaultInputModes=MarketAgent.SUPPORTED_CONTENT_TYPES,
            defaultOutputModes=MarketAgent.SUPPORTED_CONTENT_TYPES,
            capabilities=capabilities,
            skills=[skill],
        )
        server = A2AServer(
            agent_card=agent_card,
            task_manager=AgentTaskManager(agent=MarketAgent()),
            host=host,
            port=port,
        )
        server.start()
    except MissingAPIKeyError as e:
        logger.error(f"Error: {e}")
        exit(1)
    except Exception as e:
        logger.error(f"An error occurred during server startup: {e}")
        exit(1)
    
if __name__ == "__main__":
    main()