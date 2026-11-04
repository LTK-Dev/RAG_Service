import logging
import litellm
from sentence_transformers import SentenceTransformer
from typing import List
from .settings import EmbeddingSettings, LLMSettings

logger = logging.getLogger(__name__)


class EmbeddingService:
    def __init__(self, settings: EmbeddingSettings):
        """Initializes the embedding model."""
        self.settings = settings
        try:
            # Tải model 1 lần duy nhất khi khởi tạo
            self.model = SentenceTransformer(settings.model, trust_remote_code=True)
            logger.info(f"Embedding model '{settings.model}' loaded.")
        except Exception as e:
            logger.critical(
                f"CRITICAL: Failed to load embedding model: {settings.model}",
                exc_info=True,
            )
            raise

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generates embeddings for a list of texts."""
        logger.debug(f"Generating embeddings for {len(texts)} text chunks...")
        try:
            embeddings = self.model.encode(texts).tolist()
            logger.info(f"Successfully generated {len(embeddings)} embeddings.")
            return embeddings
        except Exception as e:
            logger.exception('Failed to generate embeddings')
            raise

class LLMService:
    def __init__(self, settings: LLMSettings):
        """Initializes the LLM service with API key."""
        self.settings = settings
        litellm.api_key = settings.api_key
        logger.info('LLMService initialized with provided API key.')

    def get_completion(self, prompt: str) -> str:
        """
        Calls the LLM to generate an answer.
        """
        model_name = 'gemini/gemini-2.0-flash'
        logger.debug(f"Sending prompt to LiteLLM (model: {model_name})...")
        try:
            response = litellm.completion(
                model=model_name,
                messages=[
                    {
                        'role': 'system',
                        'content': 'You are a helpful assistant. Answer based ONLY on the provided context.',
                    },
                    {'role': 'user', 'content': prompt},
                ],
                temperature=self.settings.temperature,
                top_p=self.settings.top_p,
            )
            answer = response.choices[0].message.content
            logger.info('Received completion from LiteLLM.')
            return answer
        except Exception as e:
            logger.exception('LiteLLM completion failed')
            raise e
