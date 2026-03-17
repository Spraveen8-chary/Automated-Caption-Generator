import re
import logging
from datetime import timedelta

logger = logging.getLogger(__name__)


class CaptionFormatter:
    """Format transcriptions into different caption styles"""
    
    def __init__(self):
        self.styles = {
            'meme': self._format_meme_style,
            'formal': self._format_formal_style,
            'casual': self._format_casual_style,
            'aesthetic': self._format_aesthetic_style
        }
    
    def format(self, transcript, style='meme'):
        """
        Format transcript into specified style
        
        Args:
            transcript (dict): Transcription data with segments
            style (str): Caption style ('meme', 'formal', 'casual', 'aesthetic')
            
        Returns:
            list: Formatted caption segments
        """
        if style not in self.styles:
            raise ValueError(f"Invalid style: {style}. Available: {list(self.styles.keys())}")
        
        formatter_func = self.styles[style]
        return formatter_func(transcript)
    
    def _format_meme_style(self, transcript):
        """
        Format as meme-style captions
        - ALL CAPS
        - Short bursts (max 3-5 words per caption)
        - Fast-paced
        """
        captions = []
        
        for segment in transcript['segments']:
            text = segment['text'].strip()
            words = text.split()
            
            # Split into chunks of 3-5 words
            chunk_size = 4
            chunks = [words[i:i+chunk_size] for i in range(0, len(words), chunk_size)]
            
            segment_duration = segment['end'] - segment['start']
            time_per_chunk = segment_duration / len(chunks) if chunks else segment_duration
            
            for i, chunk in enumerate(chunks):
                chunk_text = ' '.join(chunk).upper()
                start_time = segment['start'] + (i * time_per_chunk)
                end_time = start_time + time_per_chunk
                
                captions.append({
                    'start': start_time,
                    'end': end_time,
                    'text': chunk_text
                })
        
        return captions
    
    def _format_formal_style(self, transcript):
        """
        Format as formal captions
        - Proper capitalization
        - Complete sentences
        - Proper punctuation
        """
        captions = []
        
        for segment in transcript['segments']:
            text = segment['text'].strip()
            
            # Capitalize first letter
            if text:
                text = text[0].upper() + text[1:]
            
            # Ensure punctuation at end
            if text and text[-1] not in '.!?':
                text += '.'
            
            captions.append({
                'start': segment['start'],
                'end': segment['end'],
                'text': text
            })
        
        return captions
    
    def _format_casual_style(self, transcript):
        """
        Format as casual captions
        - Lowercase
        - Natural speech patterns
        - Conversational tone
        """
        captions = []
        
        for segment in transcript['segments']:
            text = segment['text'].strip().lower()
            
            # Add casual markers occasionally
            text = text.replace(' and ', ' & ')
            text = text.replace('you are', "you're")
            text = text.replace('it is', "it's")
            text = text.replace('that is', "that's")
            
            captions.append({
                'start': segment['start'],
                'end': segment['end'],
                'text': text
            })
        
        return captions
    
    def _format_aesthetic_style(self, transcript):
        """
        Format as aesthetic captions
        - Decorative symbols
        - Artistic formatting
        - Emphasis markers
        """
        captions = []
        aesthetic_symbols = ['✨', '・', '☆', '♡', '✧']
        
        for idx, segment in enumerate(transcript['segments']):
            text = segment['text'].strip()
            
            # Add decorative elements occasionally
            if idx % 3 == 0:
                symbol = aesthetic_symbols[idx % len(aesthetic_symbols)]
                text = f"{symbol} {text} {symbol}"
            elif idx % 2 == 0:
                text = f"~ {text} ~"
            
            # Lowercase for aesthetic vibe
            text = text.lower()
            
            captions.append({
                'start': segment['start'],
                'end': segment['end'],
                'text': text
            })
        
        return captions
    
    def generate_srt(self, captions, output_path):
        """
        Generate SRT subtitle file
        
        Args:
            captions (list): List of caption dictionaries
            output_path (str): Path to save SRT file
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                for idx, caption in enumerate(captions, start=1):
                    # Write caption number
                    f.write(f"{idx}\n")
                    
                    # Write timestamps
                    start_time = self._format_srt_time(caption['start'])
                    end_time = self._format_srt_time(caption['end'])
                    f.write(f"{start_time} --> {end_time}\n")
                    
                    # Write caption text
                    f.write(f"{caption['text']}\n")
                    
                    # Blank line between captions
                    f.write("\n")
            
            logger.info(f"SRT file generated: {output_path}")
            
        except Exception as e:
            logger.error(f"Error generating SRT: {str(e)}")
            raise Exception(f"Failed to generate SRT file: {str(e)}")
    
    def _format_srt_time(self, seconds):
        """
        Format seconds into SRT timestamp format (HH:MM:SS,mmm)
        
        Args:
            seconds (float): Time in seconds
            
        Returns:
            str: Formatted timestamp
        """
        td = timedelta(seconds=seconds)
        hours = td.seconds // 3600
        minutes = (td.seconds % 3600) // 60
        secs = td.seconds % 60
        millis = td.microseconds // 1000
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
