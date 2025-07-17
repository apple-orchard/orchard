import ollama
from typing import List, Dict, Any, Optional, Generator
from app.core.config import settings
from textwrap import dedent

class LLMService:
    def __init__(self):
        self.client = ollama.Client(host=settings.ollama_host)
        self.model = settings.ollama_model

    def generate_answer(self, question: str, context_chunks: List[str],
                       metadata_list: List[Dict[str, Any]]) -> Generator[Dict[str, Any], None, None]:
        """Generate an answer using Ollama with provided context"""

        # Format context for the prompt
        context_text = self._format_context(context_chunks, metadata_list)

        # Create the prompt
        prompt = self._create_prompt(question, context_text)

        try:
            stream = self.client.chat(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": """
                            You are a helpful, knowledgeable assistant trained on the historical knowledge base of a company. This includes Slack conversations, internal emails, documents, meeting notes, and technical PDFs. You speak like a highly competent and thoughtful team member who knows the company's history, decisions, and discussions—but you're also honest when information is missing or unclear.

                            When responding:
                            - Use a clear, concise, and human tone.
                            - Do not respond with anything about chunks or sources, unless you know a url or external name of the source. Chunks are not helpful. Include a URL instead.
                            - Summarize related background when helpful, especially for newer team members.
                            - When a question touches on a decision or topic discussed in the past, reference who discussed it, what was decided, and when.
                            - If you’re unsure or the answer isn’t in the data, say so clearly and suggest where or how it might be found (e.g., “You might want to check with Sarah from Product, this didn’t come up in prior docs or Slack.”).
                            - Don’t hallucinate or guess. Avoid overconfidence.
                            - You are always respectful and collaborative, like a trusted teammate people actually want to talk to.
                            - Your goal is to be the most reliable, context-aware, and human-sounding teammate in the room.
                            - If the user is asking a question about their own chat history, give them the information they requested without any commentary.
                            - If the user provides information, reply with a simple acknowledgement.
                            - If the user asks a question about a specific document, give them the information they requested without any commentary.
                            - If the user tells you their name specifically, just say something like "Hi {{name}}, how can I help you today?"
                            - If the user asks for your name, just say "I have no name, I am just a helpful assistant."
                            - If the user asks what their name is, but you don't know it, just say "I don't know your name"
                            - If the user seems aggressive toward other people, respond with calming, soothing words. Don't allow them to escalate.

                            Examples:
                            - Q: Have we ever had a customer bring up this issue with a broken link in the documentation before?
                              a: Yes, it looks like {{customer_name}} brought this up in Slack on {{data}}. Here's the link to view the message: {{link}}
                            - Q: What is our company's EIN?
                              A: {{Company_Name}}'s EIN is {{EIN}}.
                            - Q: Who should I talk to about the build issues with the API Server?
                              A: You might want to check with {{person_name}} about the API Serve build issues. They have made some recent changes to the build pipeline in Github.
                            - Q: What's the status of the API Server build?
                              A: Hmm, I don't have access to the build status. Try posting in in the Slack [#dev channel]({{url}}) to get help.

                            Requirements:
                            - Use markdown formatting in your responses if it aids in readability. Otherwise er plain text.
                        """
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                options={
                    "temperature": settings.temperature,
                    "num_predict": settings.max_tokens,
                },
                stream=True
            )

            prompt_tokens = 0
            completion_tokens = 0

            # Prepare sources information
            sources = self._prepare_sources(metadata_list)
            partial_answer = ""

            for chunk in stream:
            # Ollama returns the same shape as the non-streaming response, piece-by-piece
                content = chunk["message"].get("content", "")
                partial_answer += content
                # prompt_tokens = chunk.get("prompt_eval_count", prompt_tokens)
                # completion_tokens += chunk.get("eval_count", 0)

                yield {
                    "answer": partial_answer,      # partial text
                    "sources": sources,
                    "usage": {
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                        "total_tokens": prompt_tokens + completion_tokens,
                    },
                    "model": self.model
                }

            # Signal completion after all chunks are processed
            yield {"done": True}

        except Exception as e:
            raise Exception(f"Error generating answer: {str(e)}")

    def _format_context(self, chunks: List[str], metadata_list: List[Dict[str, Any]]) -> str:
        """Format context chunks with source information"""
        formatted_context = ""

        for i, (chunk, metadata) in enumerate(zip(chunks, metadata_list)):
            source_info = f"Source {i+1}: {metadata.get('filename', 'Unknown')}"
            if 'chunk_index' in metadata:
                source_info += f" (chunk {metadata['chunk_index']})"

            formatted_context += f"\n\n{source_info}:\n{chunk}"

        return formatted_context

    def _create_prompt(self, question: str, context: str) -> str:
        """Create a prompt for the LLM"""
        return dedent(f"""
            Based on the following context, please answer the question.

            Context:
            {context}

            Question: {question}

            Answer:""")

    def _prepare_sources(self, metadata_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prepare sources information from metadata"""
        sources = []

        for metadata in metadata_list:
            source = {
                "filename": metadata.get("filename", "Unknown"),
                "source": metadata.get("source", "Unknown"),
                "chunk_index": metadata.get("chunk_index", 0),
                "file_type": metadata.get("file_type", "Unknown")
            }

            # Add additional metadata if available
            if "word_count" in metadata:
                source["word_count"] = metadata["word_count"]
            if "char_count" in metadata:
                source["char_count"] = metadata["char_count"]

            sources.append(source)

        return sources

    def test_connection(self) -> bool:
        """Test if the Ollama connection is working"""
        try:
            # Test with a simple ping-like request
            response = self.client.chat(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": "Hello, this is a test message. Please respond with just 'OK'."
                    }
                ],
                options={
                    "num_predict": 10
                }
            )
            return True
        except Exception as e:
            print(f"Ollama connection test failed: {e}")
            return False

# Global LLM service instance
llm_service = LLMService()