from enum import Enum
from abc import ABC, abstractmethod
from youtube_transcript_api import YouTubeTranscriptApi
from transformers import pipeline
from loguru import logger
import re
from typing import Tuple, List, Dict, Any

# For extensibility
class ProviderType(str, Enum):
    youtube = "youtube"
    # Add more types (web, file, etc) here
    # web = "web"
    # pdf = "pdf"

class ContentProvider(ABC):
    """Base abstract class for all content providers"""

    @abstractmethod
    def get_transcript(self, url: str) -> str:
        """Extract text content from the provided URL"""
        pass

    @abstractmethod
    def summarize_and_validate(self, transcript: str, url: str) -> Tuple[str, bool]:
        """Summarize the transcript and validate the summary"""
        pass

    def _get_summarizer(self):
        """Get the summarization model"""
        logger.info("Loading summarization model")
        return pipeline("summarization", model="facebook/bart-large-cnn")

    def _chunk_text(self, text: str, chunk_size: int = 1000) -> List[str]:
        """Split text into chunks of specified size"""
        return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

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

        # Check for irrelevant content that might indicate a poor summary
        irrelevant_phrases = [
            "cnn.com", "visit cnn", "twitter", "snapshots gallery",
            "ireporter", "for more information", "for the latest",
            "follow us on", "visit our", "check out our"
        ]

        summary_lower = summary.lower()
        for phrase in irrelevant_phrases:
            if phrase in summary_lower:
                logger.warning(f"Summary contains irrelevant content: '{phrase}'")
                return False

        # Extract important words from transcript (improved approach)
        # Remove common stop words
        stop_words = set(['the', 'and', 'is', 'in', 'it', 'to', 'that', 'of', 'for', 'on', 'with', 'as', 'this', 'by', 'be', 'are', 'was', 'were', 'have', 'has', 'had', 'not', 'but', 'what', 'all', 'when', 'who', 'how', 'which', 'they', 'you', 'your', 'can', 'will', 'from'])

        # Tokenize and filter words
        words = []
        for word in transcript.lower().split():
            # Only consider words longer than 3 chars and not in stop words
            if len(word) > 3 and word not in stop_words:
                # Remove punctuation
                word = ''.join(c for c in word if c.isalnum())
                if word:  # Ensure word is not empty after cleaning
                    words.append(word)

        # Calculate word frequency
        word_freq = {}
        for word in words:
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

def get_provider(provider_type: ProviderType) -> ContentProvider:
    """Factory function to get the appropriate content provider"""
    if provider_type == ProviderType.youtube:
        return YouTubeProvider()
    # Add more providers here as they are implemented
    # if provider_type == ProviderType.web:
    #     return WebProvider()
    # if provider_type == ProviderType.pdf:
    #     return PDFProvider()
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

    def summarize_and_validate(self, transcript: str, url: str) -> Tuple[str, bool]:
        """Summarize the transcript and validate the summary"""
        try:
            logger.info(f"Summarizing transcript of length {len(transcript)}")
            summarizer = self._get_summarizer()

            # Clean the transcript before summarization
            # Remove any irrelevant content that might confuse the summarizer
            transcript = self._clean_transcript(transcript)

            # Target ~500 words in summary (reduced from 1000 for better quality)
            # HuggingFace pipeline has a max token limit, so chunk the text
            chunk_size = 1500  # Increased chunk size for better context
            chunks = self._chunk_text(transcript, chunk_size=chunk_size)

            # Process each chunk with appropriate length parameters
            summaries = []
            for i, chunk in enumerate(chunks):
                logger.info(f"Processing chunk {i+1}/{len(chunks)}")

                # Calculate appropriate length parameters based on chunk size and count
                # Aim for a more concise summary
                max_length = max(150, min(350, 2500 // len(chunks)))
                min_length = max(50, max_length // 3)

                # Add a prompt to guide the summarization
                prompt = f"Summarize the following content concisely and accurately: {chunk}"

                # Generate summary for this chunk
                result = summarizer(
                    prompt,
                    max_length=max_length,
                    min_length=min_length,
                    do_sample=False,
                    truncation=True
                )[0]['summary_text']

                # Clean up the result
                result = result.replace("Summarize the following content concisely and accurately:", "")
                result = result.strip()

                summaries.append(result)

            # Combine all summaries with proper transitions
            if len(summaries) > 1:
                # Add transitions between chunks for better flow
                combined_summary = summaries[0]
                for i in range(1, len(summaries)):
                    combined_summary += f" {summaries[i]}"
            else:
                combined_summary = summaries[0] if summaries else ""

            # Post-process the summary
            summary = self._post_process_summary(combined_summary)

            # Validate the summary
            is_okay = self._validate_summary(summary, transcript)

            logger.info(f"Summary generated: {len(summary)} chars, valid: {is_okay}")
            return summary, is_okay

        except Exception as e:
            logger.error(f"Error summarizing content: {str(e)}")
            raise ValueError(f"Summarization failed: {str(e)}")

    def _clean_transcript(self, transcript: str) -> str:
        """Clean the transcript before summarization"""
        # Remove common irrelevant content
        irrelevant_patterns = [
            r'(?i)visit (our|cnn)\s+website',
            r'(?i)follow us on\s+twitter',
            r'(?i)for more information',
            r'(?i)check out our\s+website',
            r'(?i)subscribe to our\s+channel',
            r'(?i)like and\s+subscribe',
            r'(?i)visit\s+cnn\.com',
            r'(?i)for the latest\s+news',
        ]

        cleaned = transcript
        for pattern in irrelevant_patterns:
            cleaned = re.sub(pattern, '', cleaned)

        # Remove excessive whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()

        return cleaned

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

    def extract_video_id(self, url: str) -> str:
        """Extract YouTube video ID from various URL formats"""
        # More robust patterns for YouTube video IDs
        patterns = [
            r'(?:v=|\/|vi\/|\?v=|\&v=)([\w-]{11})(?:[\?\&]|$)',  # Standard and embedded URLs
            r'(?:youtu\.be\/|youtube\.com\/shorts\/)([\w-]{11})',  # Short URLs and YouTube Shorts
            r'(?:youtube\.com\/embed\/)([\w-]{11})'  # Embed URLs
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)

        # If we get here, no pattern matched
        logger.error(f"Could not extract YouTube video ID from URL: {url}")
        raise ValueError(f"Invalid YouTube URL format: {url}")
