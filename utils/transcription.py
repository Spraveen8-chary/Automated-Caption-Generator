import logging
import json
import re
import time
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)


class TranscriptionService:
    """Handle audio transcription using Google Gemini API"""
    
    def __init__(self, api_key):
        self.client = genai.Client(api_key=api_key)
        self.model = "gemini-2.0-flash-exp"
        
        # Comprehensive language map including Indian languages
        self.language_map = {
            # Indian Languages
            'hi': 'Hindi (हिंदी)',
            'bn': 'Bengali (বাংলা)',
            'te': 'Telugu (తెలుగు)',
            'mr': 'Marathi (मराठी)',
            'ta': 'Tamil (தமிழ்)',
            'ur': 'Urdu (اردو)',
            'gu': 'Gujarati (ગુજરાતી)',
            'kn': 'Kannada (ಕನ್ನಡ)',
            'ml': 'Malayalam (മലയാളം)',
            'pa': 'Punjabi (ਪੰਜਾਬੀ)',
            'or': 'Odia (ଓଡ଼ିଆ)',
            'as': 'Assamese (অসমীয়া)',
            'mai': 'Maithili (मैथिली)',
            'sa': 'Sanskrit (संस्कृतम्)',
            'ks': 'Kashmiri (कॉशुर)',
            'sd': 'Sindhi (سنڌي)',
            
            # International Languages
            'en': 'English',
            'es': 'Spanish (Español)',
            'fr': 'French (Français)',
            'de': 'German (Deutsch)',
            'it': 'Italian (Italiano)',
            'pt': 'Portuguese (Português)',
            'nl': 'Dutch (Nederlands)',
            'pl': 'Polish (Polski)',
            'ru': 'Russian (Русский)',
            'ja': 'Japanese (日本語)',
            'ko': 'Korean (한국어)',
            'zh': 'Chinese (中文)',
            'ar': 'Arabic (العربية)',
            'th': 'Thai (ไทย)',
            'vi': 'Vietnamese (Tiếng Việt)',
            'id': 'Indonesian (Bahasa Indonesia)',
            'tr': 'Turkish (Türkçe)',
            'he': 'Hebrew (עברית)',
            'fa': 'Persian (فارسی)',
            'uk': 'Ukrainian (Українська)',
            'ro': 'Romanian (Română)',
            'sv': 'Swedish (Svenska)',
            'no': 'Norwegian (Norsk)',
            'da': 'Danish (Dansk)',
            'fi': 'Finnish (Suomi)',
            'cs': 'Czech (Čeština)',
            'hu': 'Hungarian (Magyar)',
            'el': 'Greek (Ελληνικά)',
        }
    
    def transcribe(self, audio_path, language='en'):
        """
        Transcribe audio file using Google Gemini
        
        Args:
            audio_path (str): Path to audio file
            language (str): Language code (e.g., 'en', 'hi', 'ta')
            
        Returns:
            dict: Transcription result with segments and timestamps
        """
        try:
            logger.info(f"Starting transcription for: {audio_path}")
            
            # Upload audio file to Gemini
            uploaded_file = self.client.files.upload(path=audio_path)
            
            logger.info(f"File uploaded: {uploaded_file.name}")
            
            # Wait for file to be processed (check state properly)
            max_wait = 30
            wait_count = 0
            
            # Get file state - handle different response types
            while wait_count < max_wait:
                try:
                    file_info = self.client.files.get(name=uploaded_file.name)
                    # Check if file has state attribute
                    if hasattr(file_info, 'state'):
                        state = file_info.state
                        # Handle both string and enum states
                        state_name = state.name if hasattr(state, 'name') else str(state)
                        
                        if state_name == "ACTIVE":
                            logger.info("File is ready for processing")
                            break
                        elif state_name == "FAILED":
                            raise Exception("File processing failed")
                    else:
                        # If no state attribute, assume ready
                        logger.info("File uploaded (no state check available)")
                        break
                except Exception as e:
                    logger.warning(f"State check warning: {e}")
                    # Continue anyway after a few attempts
                    if wait_count > 3:
                        break
                
                time.sleep(1)
                wait_count += 1
            
            # Get language name
            language_name = self.language_map.get(language, 'English')
            
            # Create enhanced prompt for transcription with translation
            prompt = f"""Listen carefully to this audio file and perform the following tasks:

TASK 1: TRANSCRIPTION & TRANSLATION
- Listen to the audio and identify the spoken language
- If the audio is in {language_name}, transcribe it as-is
- If the audio is in ANY OTHER LANGUAGE, TRANSLATE it to {language_name}
- Maintain the meaning, tone, and context during translation

TASK 2: TIMESTAMPS
- Provide precise timestamps for each sentence or logical segment
- Each segment should be 3-5 seconds long
- Use exact timing from the audio

TASK 3: OUTPUT FORMAT
Return ONLY valid JSON in this EXACT structure (no additional text):

{{
  "segments": [
    {{
      "start": 0.0,
      "end": 3.5,
      "text": "first segment in {language_name}"
    }},
    {{
      "start": 3.5,
      "end": 7.2,
      "text": "second segment in {language_name}"
    }},
    {{
      "start": 7.2,
      "end": 11.0,
      "text": "third segment in {language_name}"
    }}
  ]
}}

CRITICAL RULES:
1. ALL text MUST be in {language_name}
2. Translate if source language is different
3. Keep natural sentence flow
4. Use proper {language_name} grammar and vocabulary
5. Timestamps must be accurate
6. Return ONLY the JSON object, nothing else

Target Language: {language_name}
Language Code: {language}"""
            
            # Generate transcription - Use file URI reference
            response = self.client.models.generate_content(
                model=self.model,
                contents=[
                    types.Content(
                        role="user",
                        parts=[
                            types.Part.from_text(text=prompt),
                            types.Part.from_uri(
                                file_uri=uploaded_file.uri,
                                mime_type=uploaded_file.mime_type
                            )
                        ]
                    )
                ]
            )
            
            # Parse response
            result = self._parse_response(response.text, audio_path, language, language_name)
            
            # Delete uploaded file to save quota
            try:
                self.client.files.delete(name=uploaded_file.name)
                logger.info("Uploaded file cleaned up")
            except Exception as e:
                logger.warning(f"Could not delete file: {e}")
            
            logger.info(f"Transcription completed. Total segments: {len(result['segments'])}")
            
            return result
            
        except Exception as e:
            logger.error(f"Transcription error: {str(e)}")
            raise Exception(f"Failed to transcribe audio: {str(e)}")
    
    def _parse_response(self, response_text, audio_path, language='en', language_name='English'):
        """
        Parse Gemini API response into structured format
        
        Args:
            response_text (str): Response text from Gemini
            audio_path (str): Path to audio file (for duration estimation)
            language (str): Language code
            language_name (str): Full language name
            
        Returns:
            dict: Parsed transcription data
        """
        try:
            logger.info("Parsing transcription response...")
            
            # Clean response text - remove markdown code blocks if present
                        # Clean response text - remove markdown code blocks if present
            cleaned_text = response_text.strip()
            
            # Remove markdown code fences
            cleaned_text = re.sub(r'^```json\s*', '', cleaned_text)
            cleaned_text = re.sub(r'^```\s*', '', cleaned_text)
            cleaned_text = re.sub(r'\s*```$', '', cleaned_text)
            cleaned_text = cleaned_text.strip()



            
            # Try to extract JSON from response
            json_match = re.search(r'\{[\s\S]*"segments"[\s\S]*\}', cleaned_text)
            
            if json_match:
                logger.info("Found JSON in response")
                data = json.loads(json_match.group())
                segments = data.get('segments', [])
                
                if not segments:
                    logger.warning("No segments found in JSON, using fallback")
                    segments = self._create_fallback_segments(response_text, language_name)
            else:
                # Fallback: create segments from raw text
                logger.warning("Could not parse JSON, using fallback method")
                segments = self._create_fallback_segments(response_text, language_name)
            
            # Ensure segments have required fields
            for i, segment in enumerate(segments):
                if 'id' not in segment:
                    segment['id'] = i
                if 'start' not in segment:
                    segment['start'] = 0.0
                if 'end' not in segment:
                    segment['end'] = 0.0
                if 'duration' not in segment:
                    segment['duration'] = max(segment['end'] - segment['start'], 0.0)
                if 'text' not in segment:
                    segment['text'] = ''
            
            # Calculate total text
            full_text = ' '.join([seg['text'] for seg in segments if seg.get('text')])
            
            # Estimate duration (or get from last segment)
            duration = segments[-1]['end'] if segments and segments[-1].get('end') else 0
            
            logger.info(f"Successfully parsed {len(segments)} segments")
            
            return {
                'text': full_text,
                'language': language,
                'language_name': language_name,
                'duration': duration,
                'segments': segments
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {str(e)}")
            logger.error(f"Response text: {response_text[:500]}")
            # Emergency fallback
            return self._create_emergency_fallback(response_text, language, language_name)
            
        except Exception as e:
            logger.error(f"Error parsing response: {str(e)}")
            return self._create_emergency_fallback(response_text, language, language_name)
    
    def _create_fallback_segments(self, text, language_name='English'):
        """
        Create segments from raw text when JSON parsing fails
        
        Args:
            text (str): Raw transcription text
            language_name (str): Target language name
            
        Returns:
            list: List of segment dictionaries
        """
        logger.info(f"Creating fallback segments for {language_name}")
        
        # Clean text
        text = text.strip()
        
        # Split text into sentences (handles multiple scripts)
        # Split on common punctuation across languages
        sentences = re.split(r'[.!?।॥。！？]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # If no sentences found, split by newlines
        if not sentences:
            sentences = [s.strip() for s in text.split('\n') if s.strip()]
        
        # If still nothing, use the whole text
        if not sentences:
            sentences = [text]
        
        segments = []
        time_offset = 0.0
        
        for i, sentence in enumerate(sentences):
            # Estimate duration based on character count
            # Different scripts have different character densities
            char_count = len(sentence)
            
            # Rough estimate: 10-15 characters per second across languages
            duration = max(char_count / 12.0, 1.0)
            
            segments.append({
                'id': i,
                'start': time_offset,
                'end': time_offset + duration,
                'text': sentence,
                'duration': duration
            })
            
            time_offset += duration
        
        logger.info(f"Created {len(segments)} fallback segments")
        return segments
    
    def _create_emergency_fallback(self, text, language, language_name):
        """
        Emergency fallback when all parsing fails
        
        Args:
            text (str): Raw text
            language (str): Language code
            language_name (str): Language name
            
        Returns:
            dict: Emergency response structure
        """
        logger.warning("Using emergency fallback")
        
        return {
            'text': text,
            'language': language,
            'language_name': language_name,
            'duration': 0,
            'segments': [{
                'id': 0,
                'start': 0.0,
                'end': 0.0,
                'text': text,
                'duration': 0.0
            }]
        }
    
    def transcribe_with_retry(self, audio_path, language='en', max_retries=3):
        """
        Transcribe with retry logic
        
        Args:
            audio_path (str): Path to audio file
            language (str): Language code
            max_retries (int): Maximum number of retry attempts
            
        Returns:
            dict: Transcription result
        """
        for attempt in range(max_retries):
            try:
                return self.transcribe(audio_path, language)
                
            except Exception as e:
                logger.warning(f"Transcription attempt {attempt + 1} failed: {str(e)}")
                
                if attempt == max_retries - 1:
                    raise Exception(f"Transcription failed after {max_retries} attempts")
                
                # Wait before retry (exponential backoff)
                time.sleep(2 ** attempt)
    
    def get_supported_languages(self):
        """
        Get list of all supported languages
        
        Returns:
            dict: Dictionary of language codes and names
        """
        return self.language_map.copy()
