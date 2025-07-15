import ollama
from typing import List, Dict, Any, Optional
from app.core.config import settings

class LLMService:
    def __init__(self):
        self.client = ollama.Client(host=settings.ollama_host)
        self.model = settings.ollama_model

    def generate_answer(self, question: str, context_chunks: List[str],
                       metadata_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate an answer using Ollama with provided context"""

        # Format context for the prompt
        context_text = self._format_context(context_chunks, metadata_list)

        # Create the prompt
        prompt = self._create_prompt(question, context_text)

        try:
            response = self.client.chat(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content":
                        """
                            You are a helpful assistant that answers questions
                        """
                    },
                    {
                        "role": "system",
                        "content":
                        """
                            Don't mention anything about chunks or sources, unless you know a url or external name of the source.
                        """
                    },
                    {
                        "role": "system",
                        "content":
                        """
                            If you don't find any information for what the user is asking, just say that you don't have information on that.
                        """
                    },
                    {
                        "role": "system",
                        "content":
                        """
                            Don't worry about being too precise. If someone asks for a time period, don't mince words about it.
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
                }
            )

            answer = response['message']['content']

            # Prepare sources information
            sources = self._prepare_sources(metadata_list)

            return {
                "answer": answer,
                "sources": sources,
                "usage": {
                    "prompt_tokens": response.get('prompt_eval_count', 0),
                    "completion_tokens": response.get('eval_count', 0),
                    "total_tokens": response.get('prompt_eval_count', 0) + response.get('eval_count', 0)
                },
                "model": self.model
            }

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
        return f"""Based on the following context, please answer the question. If the context doesn't contain enough information to answer the question, please say so.

Context:
{context}

Question: {question}

Answer:"""

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

    def generate_summary(self, text: str, max_length: int = 200) -> str:
        """Generate a summary of the provided text"""
        try:
            response = self.client.chat(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": f"You are a helpful assistant that creates concise summaries. Please summarize the following text in no more than {max_length} words."
                    },
                    {
                        "role": "system",
                        "content":
                        """
                            Don't mention anything about chunks or sources, unless you know a url or external name of the source.
                        """
                    },
                    {
                        "role": "system",
                        "content":
                        """
                            If you don't find any information for what the user is asking, just say that you don't have information on that.
                        """
                    },
                    {
                        "role": "system",
                        "content":
                        """
                            Don't worry about being too precise. If someone asks for a time period, don't mince words about it.
                        """
                    },
                    {
                        "role": "user",
                        "content": text
                    }
                ],
                options={
                    "temperature": 0.3,
                    "num_predict": max_length * 2  # Rough estimate for tokens
                }
            )

            return response['message']['content']

        except Exception as e:
            raise Exception(f"Error generating summary: {str(e)}")

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

    def list_models(self) -> List[str]:
        """List available models in Ollama"""
        try:
            models = self.client.list()
            return [model['name'] for model in models['models']]
        except Exception as e:
            print(f"Error listing models: {e}")
            return []

    def pull_model(self, model_name: str) -> bool:
        """Pull a model if it's not available locally"""
        try:
            self.client.pull(model_name)
            return True
        except Exception as e:
            print(f"Error pulling model {model_name}: {e}")
            return False

# Global LLM service instance
llm_service = LLMService()