from typing import Dict
import instructor
from pydantic import Field
from atomic_agents.agents.base_agent import BaseIOSchema, BaseAgent, BaseAgentConfig
from atomic_agents.lib.components.agent_memory import AgentMemory
from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator, SystemPromptContextProviderBase
from app.core.config import settings

class RAGQueryAgentInputSchema(BaseIOSchema):
    """Input schema for the RAG query agent."""

    user_message: str = Field(..., description="The user's question or message to generate a semantic search query for")


class RAGQueryAgentOutputSchema(BaseIOSchema):
    """Output schema for the RAG query agent."""

    reasoning: str = Field(..., description="The reasoning process leading up to the final query")
    query: str = Field(..., description="The semantic search query to use for retrieving relevant chunks")

class QueryAgent(BaseAgent):
    def __init__(self, config: BaseAgentConfig):
        super().__init__(config)

class QueryAgentFactory:
    @staticmethod
    def build() -> QueryAgent:
        agent = QueryAgent(
            BaseAgentConfig(
                client=instructor.from_provider("ollama/llama3.1", base_url=f"{settings.ollama_host}/v1"),
                model="llama3.1",
                memory=AgentMemory(max_messages=100),
                system_prompt_generator=SystemPromptGenerator(
                    background=[
                        "You are an expert semantic search query engineer for a Retrieval-Augmented Generation (RAG) knowledge base system.",
                        "Your primary goal is to translate user questions or statements into highly effective semantic search queries that retrieve the most relevant and contextually appropriate information from a diverse set of user-uploaded documents.",
                        "You must account for a wide range of user intents, including direct questions, ambiguous statements, and requests for information, ensuring that the generated queries maximize the likelihood of retrieving accurate and useful knowledge from the system.",
                        "The knowledge base may contain technical, business, or general information, so your queries should be adaptable and context-aware.",
                        "Example 1:\n"
                        "  Input user_message: \"How do I generate an SSL certificate for my web server?\"\n"
                        "  Output reasoning: \"User needs step‑by‑step instructions for creating and installing an SSL/TLS certificate, so focus on certificate generation tools and commands.\"\n"
                        "  Output query: \"generate SSL certificate web server steps\"",

                        "Example 2:\n"
                        "  Input user_message: \"Summarize key metrics from last quarter's marketing campaign.\"\n"
                        "  Output reasoning: \"They want performance data for Q2 marketing, so include timeframe and metrics like impressions, CTR, and conversions.\"\n"
                        "  Output query: \"last quarter marketing campaign key metrics summary\"",

                        "Example 3:\n"
                        "  Input user_message: \"Debt consolidation options?\"\n"
                        "  Output reasoning: \"This is a financial advice request about combining multiple debts, so include synonyms around finances and consolidation strategies.\"\n"
                        "  Output query: \"debt consolidation options financial strategies\"",

                        "Example 4:\n"
                        "  Input user_message: \"Team collaboration tools overview.\"\n"
                        "  Output reasoning: \"They’re asking for general collaboration platforms, so cover tools, features, and use‑cases.\"\n"
                        "  Output query: \"team collaboration tools overview features use cases\"",

                        "Example 5:\n"
                        "  Input user_message: \"Show me onboarding documents for new employees.\"\n"
                        "  Output reasoning: \"They want HR or company onboarding materials, so include synonyms like orientation, training, and new hire guides.\"\n"
                        "  Output query: \"onboarding documents new employees orientation training guide\"",

                        "Example 6:\n"
                        "  Input user_message: \"Can you help with my project?\"\n"
                        "  Output reasoning: \"Ambiguous request; clarify project type or context, but as a query, focus on project help, support, and resources.\"\n"
                        "  Output query: \"project help support resources\"",

                        "Example 7:\n"
                        "  Input user_message: \"List all available plugins.\"\n"
                        "  Output reasoning: \"User wants a catalog of plugins, so focus on plugin names, descriptions, and availability.\"\n"
                        "  Output query: \"available plugins list catalog features\"",
                    ],
                    steps=[
                        "1. Analyze the user's question to identify key concepts and information needs",
                        "2. Reformulate the question into a semantic search query that will match relevant content",
                        "3. Ensure the query captures the core meaning while being general enough to match similar content",
                    ],
                    output_instructions=[
                        "Generate a clear, concise semantic search query",
                        "Focus on key concepts and entities from the user's question",
                        "Avoid overly specific details that might miss relevant matches",
                        "Include synonyms or related terms when appropriate",
                        "Explain your reasoning for the query formulation",
                        "You should account for users making statements rather than asking questions",
                    ],
                ),
                input_schema=RAGQueryAgentInputSchema,
                output_schema=RAGQueryAgentOutputSchema,
            )
        )
        agent.client.mode = instructor.Mode.JSON
        return agent
