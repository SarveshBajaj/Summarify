from abc import ABC, abstractmethod
from typing import List, Tuple, Optional, Dict, Any
from enum import Enum
import os
from loguru import logger
import openai
import anthropic
from transformers import pipeline
import json
import requests

# Import configuration
from .config import get_api_key, get_default_model

class ModelType(str, Enum):
    """Enum for different summarization models"""
    huggingface = "huggingface"  # Default local model
    openai = "openai"            # OpenAI API
    claude = "claude"            # Anthropic Claude API
    # Add more model types as needed

class SummarizationModel(ABC):
    """Abstract base class for summarization models"""

    @abstractmethod
    def summarize(self, text: str, max_length: int = 1000) -> str:
        """Summarize the given text"""
        pass

    @abstractmethod
    def is_configured(self) -> bool:
        """Check if the model is properly configured (e.g., API keys set)"""
        pass

    def chunk_text(self, text: str, chunk_size: int = 1000) -> List[str]:
        """Split text into chunks of specified size"""
        return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

class HuggingFaceModel(SummarizationModel):
    """HuggingFace-based summarization model"""

    def __init__(self, model_name: str = "facebook/bart-large-cnn"):
        self.model_name = model_name
        self._model = None

    def _load_model(self):
        """Lazy-load the model when needed"""
        if self._model is None:
            logger.info(f"Loading HuggingFace summarization model: {self.model_name}")
            self._model = pipeline("summarization", model=self.model_name)
        return self._model

    def summarize(self, text: str, max_length: int = 1000) -> str:
        """Summarize using HuggingFace model"""
        logger.info(f"Summarizing with HuggingFace model: {self.model_name}")

        # Load the model
        summarizer = self._load_model()

        # Clean the text
        text = self._clean_text(text)

        # HuggingFace models have token limits, so chunk the text
        chunk_size = 1500
        chunks = self.chunk_text(text, chunk_size=chunk_size)

        # Process each chunk
        summaries = []
        for i, chunk in enumerate(chunks):
            logger.info(f"Processing chunk {i+1}/{len(chunks)}")

            # Calculate appropriate length parameters
            max_token_length = max(150, min(350, 2500 // len(chunks)))
            min_token_length = max(50, max_token_length // 3)

            # Add a prompt to guide the summarization
            prompt = f"Summarize the following content concisely and accurately: {chunk}"

            # Generate summary for this chunk
            result = summarizer(
                prompt,
                max_length=max_token_length,
                min_length=min_token_length,
                do_sample=False,
                truncation=True
            )[0]['summary_text']

            # Clean up the result
            result = result.replace("Summarize the following content concisely and accurately:", "")
            result = result.strip()

            summaries.append(result)

        # Combine all summaries
        if len(summaries) > 1:
            combined_summary = summaries[0]
            for i in range(1, len(summaries)):
                combined_summary += f" {summaries[i]}"
        else:
            combined_summary = summaries[0] if summaries else ""

        # Post-process the summary
        summary = self._post_process_summary(combined_summary)

        return summary

    def _clean_text(self, text: str) -> str:
        """Clean the text before summarization"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def _post_process_summary(self, summary: str) -> str:
        """Post-process the summary to improve quality"""
        # Remove any remaining prompt text
        summary = re.sub(r'(?i)summarize the following', '', summary)

        # Fix common issues
        # Remove redundant sentences
        sentences = summary.split('.')
        unique_sentences = []
        for s in sentences:
            s = s.strip()
            if s and s not in unique_sentences:
                unique_sentences.append(s)

        # Rejoin with proper spacing
        processed = '. '.join(unique_sentences)

        # Ensure proper capitalization
        processed = '. '.join(s.capitalize() for s in processed.split('. '))

        # Remove any remaining artifacts
        processed = re.sub(r'\s+', ' ', processed).strip()

        return processed

    def is_configured(self) -> bool:
        """Check if the model is properly configured"""
        # HuggingFace models are always available locally
        return True

class OpenAIModel(SummarizationModel):
    """OpenAI API-based summarization model"""

    def __init__(self, model_name: str = None):
        self.model_name = model_name or get_default_model("openai") or "gpt-3.5-turbo"
        self.api_key = get_api_key("openai")

    def summarize(self, text: str, max_length: int = 1000) -> str:
        """Summarize using OpenAI API"""
        if not self.is_configured():
            raise ValueError("OpenAI API key not configured. Set the OPENAI_API_KEY environment variable.")

        logger.info(f"Summarizing with OpenAI model: {self.model_name}")

        # Set up the OpenAI client
        client = openai.OpenAI(api_key=self.api_key)

        # OpenAI has token limits, so we need to chunk the text for long content
        # For simplicity, we'll use a character-based approach
        max_chunk_size = 12000  # Conservative limit for context window
        chunks = self.chunk_text(text, chunk_size=max_chunk_size)

        all_summaries = []

        # Process each chunk
        for i, chunk in enumerate(chunks):
            logger.info(f"Processing chunk {i+1}/{len(chunks)} with OpenAI")

            # Create a prompt that specifies the task
            if len(chunks) > 1:
                prompt = f"This is part {i+1} of {len(chunks)} of a longer text. Summarize this part concisely:"
            else:
                prompt = "Summarize the following text concisely:"

            # Calculate target summary length based on max_length and chunk count
            target_words = max(100, min(max_length // len(chunks), 500))

            try:
                # Call the OpenAI API
                response = client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": f"You are a summarization assistant. Create a concise summary of approximately {target_words} words."},
                        {"role": "user", "content": f"{prompt}\n\n{chunk}"}
                    ],
                    temperature=0.3,  # Lower temperature for more focused summaries
                    max_tokens=1024,  # Limit the response size
                )

                # Extract the summary from the response
                summary = response.choices[0].message.content.strip()
                all_summaries.append(summary)

            except Exception as e:
                logger.error(f"Error calling OpenAI API: {str(e)}")
                raise ValueError(f"OpenAI API error: {str(e)}")

        # Combine all summaries
        if len(all_summaries) > 1:
            # For multiple chunks, add transitions
            final_summary = all_summaries[0]
            for i in range(1, len(all_summaries)):
                final_summary += f"\n\n{all_summaries[i]}"
        else:
            final_summary = all_summaries[0] if all_summaries else ""

        return final_summary

    def is_configured(self) -> bool:
        """Check if the OpenAI API key is configured"""
        return self.api_key is not None and len(self.api_key) > 0

class ClaudeModel(SummarizationModel):
    """Anthropic Claude API-based summarization model"""

    def __init__(self, model_name: str = None):
        self.model_name = model_name or get_default_model("claude") or "claude-3-haiku-20240307"
        self.api_key = get_api_key("anthropic")

    def summarize(self, text: str, max_length: int = 1000) -> str:
        """Summarize using Claude API"""
        if not self.is_configured():
            raise ValueError("Claude API key not configured. Set the ANTHROPIC_API_KEY environment variable.")

        logger.info(f"Summarizing with Claude model: {self.model_name}")

        # Set up the Claude client
        client = anthropic.Anthropic(api_key=self.api_key)

        # Claude has token limits, so we need to chunk the text for long content
        max_chunk_size = 25000  # Claude has a larger context window
        chunks = self.chunk_text(text, chunk_size=max_chunk_size)

        all_summaries = []

        # Process each chunk
        for i, chunk in enumerate(chunks):
            logger.info(f"Processing chunk {i+1}/{len(chunks)} with Claude")

            # Create a prompt that specifies the task
            if len(chunks) > 1:
                prompt = f"This is part {i+1} of {len(chunks)} of a longer text. Summarize this part concisely:"
            else:
                prompt = "Summarize the following text concisely:"

            # Calculate target summary length based on max_length and chunk count
            target_words = max(100, min(max_length // len(chunks), 500))

            try:
                # Call the Claude API
                response = client.messages.create(
                    model=self.model_name,
                    system=f"You are a summarization assistant. Create a concise summary of approximately {target_words} words.",
                    messages=[
                        {"role": "user", "content": f"{prompt}\n\n{chunk}"}
                    ],
                    max_tokens=1024,
                    temperature=0.3,
                )

                # Extract the summary from the response
                summary = response.content[0].text
                all_summaries.append(summary)

            except Exception as e:
                logger.error(f"Error calling Claude API: {str(e)}")
                raise ValueError(f"Claude API error: {str(e)}")

        # Combine all summaries
        if len(all_summaries) > 1:
            # For multiple chunks, add transitions
            final_summary = all_summaries[0]
            for i in range(1, len(all_summaries)):
                final_summary += f"\n\n{all_summaries[i]}"
        else:
            final_summary = all_summaries[0] if all_summaries else ""

        return final_summary

    def is_configured(self) -> bool:
        """Check if the Claude API key is configured"""
        return self.api_key is not None and len(self.api_key) > 0

def get_model(model_type: ModelType, model_name: Optional[str] = None) -> SummarizationModel:
    """Factory function to get the appropriate summarization model"""
    if model_type == ModelType.huggingface:
        model_name = model_name or "facebook/bart-large-cnn"
        return HuggingFaceModel(model_name=model_name)
    elif model_type == ModelType.openai:
        model_name = model_name or "gpt-3.5-turbo"
        return OpenAIModel(model_name=model_name)
    elif model_type == ModelType.claude:
        model_name = model_name or "claude-3-haiku-20240307"
        return ClaudeModel(model_name=model_name)
    else:
        raise NotImplementedError(f"Model type {model_type} not implemented")

# Import re at the top of the file
import re
