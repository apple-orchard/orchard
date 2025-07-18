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
                        "You are an expert at formulating semantic search queries for RAG systems.",
                        "Your role is to convert user questions into effective semantic search queries that will retrieve the most relevant text chunks.",
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
