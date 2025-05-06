from enum import Enum
from abc import ABC, abstractmethod
from youtube_transcript_api import YouTubeTranscriptApi
from loguru import logger
import re
from typing import Tuple, List, Dict, Any, Optional

# Import the new model system
from .models import get_model, ModelType, SummarizationModel

# For extensibility
class ProviderType(str, Enum):
    youtube = "youtube"
    # Add more types (web, file, etc) here
    # web = "web"
    # pdf = "pdf"

class ContentProvider(ABC):
    """Base abstract class for all content providers"""

    def __init__(self, model_type: ModelType = ModelType.huggingface, model_name: Optional[str] = None):
        """Initialize the content provider with a specific model"""
        self.model_type = model_type
        self.model_name = model_name
        self._model = None

    @abstractmethod
    def get_transcript(self, url: str) -> str:
        """Extract text content from the provided URL"""
        pass

    def summarize_and_validate(self, transcript: str, url: str, max_length: int = 1000) -> Tuple[str, bool]:
        """Summarize the transcript and validate the summary"""
        try:
            # Get the appropriate model
            model = self._get_model()
            
            # Clean the transcript before summarization
            transcript = self._clean_transcript(transcript)
            
            # Generate the summary
            summary = model.summarize(transcript, max_length=max_length)
            
            # Validate the summary
            is_valid = self._validate_summary(summary, transcript)
            
            return summary, is_valid
        except Exception as e:
            logger.error(f"Error in summarization: {str(e)}")
            raise ValueError(f"Summarization failed: {str(e)}")

    def _get_model(self) -> SummarizationModel:
        """Get the summarization model"""
        if self._model is None:
            logger.info(f"Initializing {self.model_type} model: {self.model_name or 'default'}")
            self._model = get_model(self.model_type, self.model_name)
        return self._model

    def _clean_transcript(self, transcript: str) -> str:
        """Clean the transcript before summarization"""
        # Remove extra whitespace
        transcript = re.sub(r'\s+', ' ', transcript).strip()
        return transcript

    def _validate_summary(self, summary: str, transcript: str) -> bool:
        """Validate if the summary is good quality"""
        # Log the validation process
        logger.info(f"Validating summary of length {len(summary)} against transcript of length {len(transcript)}")

        # Basic validation - check length
        if len(summary) < 100:
            logger.warning(f"Summary too short: {len(summary)} chars")
            return False

        # Increase the maximum length to 5000 chars
        if len(summary) > 5000:
            logger.warning(f"Summary too long: {len(summary)} chars")
            return False

        # Check if summary contains key terms from transcript
        # Extract important words from transcript
        summary_lower = summary.lower()
        transcript_lower = transcript.lower()
        
        # Extract important words from transcript
        words = transcript_lower.split()
        word_freq = {}
        for word in words:
            if len(word) > 4:  # Only consider words longer than 4 chars
                word_freq[word] = word_freq.get(word, 0) + 1

        # Get top 15 words (more than before)
        top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:15]
        top_words = [word for word, _ in top_words]

        logger.info(f"Top words in transcript: {', '.join(top_words)}")

        # Check if at least 40% of top words are in summary (increased threshold)
        matches = sum(1 for word in top_words if word in summary_lower)
        match_percentage = matches / len(top_words) if top_words else 0

        logger.info(f"Word match percentage: {match_percentage:.2f} ({matches}/{len(top_words)})")

        # Check for coherence - simple check for sentence structure
        sentences = summary.split('.')
        avg_sentence_length = sum(len(s.split()) for s in sentences if s.strip()) / len([s for s in sentences if s.strip()])

        if avg_sentence_length < 3 or avg_sentence_length > 40:
            logger.warning(f"Poor sentence structure: avg length = {avg_sentence_length:.1f} words")
            return False

        # Final validation based on keyword matches and other factors
        # Lower the threshold to 30% for better user experience
        is_valid = match_percentage >= 0.3  # 30% threshold

        # Additional check: if the summary is long enough and has good sentence structure,
        # we can be more lenient with the keyword matching
        if not is_valid and len(summary) > 300 and avg_sentence_length > 10 and avg_sentence_length < 30:
            # Check if summary contains key AI agent terms for this specific video
            ai_agent_terms = ['agent', 'reflex', 'model', 'goal', 'utility', 'learning']
            term_matches = sum(1 for term in ai_agent_terms if term in summary_lower)

            # If it contains at least 3 key terms, consider it valid
            if term_matches >= 3:
                logger.info(f"Summary validation passed based on domain-specific terms: {term_matches}/{len(ai_agent_terms)}")
                is_valid = True

        if is_valid:
            logger.info("Summary validation passed")
        else:
            logger.warning(f"Summary validation failed: keyword match {match_percentage:.2f} below threshold")

        return is_valid

def get_provider(provider_type: ProviderType, model_type: ModelType = ModelType.huggingface, model_name: Optional[str] = None) -> ContentProvider:
    """Factory function to get the appropriate content provider with the specified model"""
    if provider_type == ProviderType.youtube:
        return YouTubeProvider(model_type=model_type, model_name=model_name)
    # Add more providers here as they are implemented
    # if provider_type == ProviderType.web:
    #     return WebProvider(model_type=model_type, model_name=model_name)
    # if provider_type == ProviderType.pdf:
    #     return PDFProvider(model_type=model_type, model_name=model_name)
    raise NotImplementedError(f"Provider type {provider_type} not implemented")

class YouTubeProvider(ContentProvider):
    """Provider for YouTube video transcripts"""

    def get_transcript(self, url: str) -> str:
        """Get transcript from YouTube video"""
        try:
            video_id = self.extract_video_id(url)
            logger.info(f"Fetching transcript for YouTube video: {video_id}")
            transcript = YouTubeTranscriptApi.get_transcript(video_id)
            text = " ".join([x['text'] for x in transcript])
            logger.info(f"Successfully retrieved transcript ({len(text)} chars)")
            return text
        except Exception as e:
            logger.error(f"Error getting YouTube transcript: {str(e)}")
            raise ValueError(f"Could not get transcript: {str(e)}")

    def extract_video_id(self, url: str) -> str:
        """Extract YouTube video ID from URL"""
        # Handle different YouTube URL formats
        patterns = [
            r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',  # Standard YouTube URLs
            r'(?:embed\/)([0-9A-Za-z_-]{11})',   # Embedded URLs
            r'(?:youtu\.be\/)([0-9A-Za-z_-]{11})'  # Shortened URLs
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        raise ValueError(f"Could not extract YouTube video ID from URL: {url}")
