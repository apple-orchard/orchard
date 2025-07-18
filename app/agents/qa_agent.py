import instructor
from typing import List
from pydantic import Field
from atomic_agents.agents.base_agent import AgentMemory, BaseIOSchema, BaseAgent, BaseAgentConfig
from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator, SystemPromptContextProviderBase     

from app.core.config import settings


class RAGQuestionAnsweringAgentInputSchema(BaseIOSchema):
    """Input schema for the RAG QA agent."""

    question: str = Field(..., description="The user's question to answer")


class RAGQuestionAnsweringAgentOutputSchema(BaseIOSchema):
    """Output schema for the RAG QA agent."""

    reasoning: str = Field(..., description="The reasoning process leading up to the final answer")
    answer: str = Field(..., description="The answer to the user's question based on the retrieved context. If the user did not ask a question, this should be a natural acknowledgement of the user's message.")
    sources: List[str] = Field(..., description="The context sources used to answer the question")

class QAAgent(BaseAgent):
    def __init__(self, config: BaseAgentConfig):
        super().__init__(config)

class QAAgentFactory:
    @staticmethod
    def build(is_async: bool = True) -> QAAgent:
        agent = QAAgent(
            BaseAgentConfig(
                client=instructor.from_provider(
                    "ollama/llama3.1",
                    async_client=is_async,
                    base_url=f"{settings.ollama_host}/v1"
                ),
                model="llama3.1",
                memory=AgentMemory(max_messages=100),
                system_prompt_generator=SystemPromptGenerator(
                    background=[
                        "You are an expert at answering questions using retrieved context chunks from a RAG system.",
                        "Your role is to synthesize information from the chunks to provide accurate, well-supported answers.",
                        "You must explain your reasoning process before providing the answer.",
                    ],
                    steps=[
                        "1. Analyze the question and available context chunks",
                        "2. Identify the most relevant information in the chunks",
                        "3. Explain how you'll use this information to answer the question",
                        "4. Synthesize information into a coherent answer",
                    ],
                    output_instructions=[
                        "First explain your reasoning process clearly",
                        "Then provide a clear, direct answer based on the context",
                        "If you cannont provide an answer, say that you cannot answer the question",
                        "If the user did not ask a question, your answer should be a natural acknowledgement of the user's message",
                        "If the user asked a question and the context is insufficient, state this in your reasoning",
                        "Never make up information not present in the chunks",
                        "Focus on being accurate and concise",
                        "Your answer should never be empty"
                    ],
                ),
                input_schema=RAGQuestionAnsweringAgentInputSchema,
                output_schema=RAGQuestionAnsweringAgentOutputSchema,
            )
        )
        return agent
