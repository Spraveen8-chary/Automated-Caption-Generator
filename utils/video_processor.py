import os
import logging
from moviepy.editor import VideoFileClip

logger = logging.getLogger(__name__)


class VideoProcessor:
    """Handle video processing operations"""
    
    def __init__(self, upload_folder):
        self.upload_folder = upload_folder
        self.audio_format = 'mp3'
    
    def extract_audio(self, video_path):
        """
        Extract audio from video file
        
        Args:
            video_path (str): Path to video file
            
        Returns:
            str: Path to extracted audio file
        """
        try:
            logger.info(f"Loading video: {video_path}")
            
            # Load video file
            video = VideoFileClip(video_path)
            
            # Generate audio filename
            audio_filename = f"{os.path.splitext(os.path.basename(video_path))[0]}.{self.audio_format}"
            audio_path = os.path.join(self.upload_folder, audio_filename)
            
            # Extract audio
            logger.info(f"Extracting audio to: {audio_path}")
            video.audio.write_audiofile(
                audio_path,
                codec='libmp3lame',
                logger=None  # Suppress moviepy logs
            )
            
            # Close video file
            video.close()
            
            logger.info(f"Audio extracted successfully: {audio_path}")
            return audio_path
            
        except Exception as e:
            logger.error(f"Error extracting audio: {str(e)}")
            raise Exception(f"Failed to extract audio: {str(e)}")
    
    def get_video_duration(self, video_path):
        """
        Get video duration in seconds
        
        Args:
            video_path (str): Path to video file
            
        Returns:
            float: Duration in seconds
        """
        try:
            video = VideoFileClip(video_path)
            duration = video.duration
            video.close()
            return duration
            
        except Exception as e:
            logger.error(f"Error getting video duration: {str(e)}")
            return 0
    
    def validate_video(self, video_path):
        """
        Validate video file
        
        Args:
            video_path (str): Path to video file
            
        Returns:
            dict: Validation result with status and message
        """
        try:
            if not os.path.exists(video_path):
                return {'valid': False, 'message': 'Video file not found'}
            
            # Try to load video
            video = VideoFileClip(video_path)
            
            # Check if video has audio
            if video.audio is None:
                video.close()
                return {'valid': False, 'message': 'Video has no audio track'}
            
            # Get video info
            duration = video.duration
            fps = video.fps
            size = video.size
            
            video.close()
            
            return {
                'valid': True,
                'message': 'Video is valid',
                'info': {
                    'duration': duration,
                    'fps': fps,
                    'resolution': f"{size[0]}x{size[1]}"
                }
            }
            
        except Exception as e:
            logger.error(f"Video validation error: {str(e)}")
            return {'valid': False, 'message': f'Invalid video file: {str(e)}'}
    
    def cleanup_file(self, filepath):
        """
        Delete file from disk
        
        Args:
            filepath (str): Path to file to delete
        """
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                logger.info(f"Cleaned up file: {filepath}")
            else:
                logger.warning(f"File not found for cleanup: {filepath}")
                
        except Exception as e:
            logger.error(f"Error cleaning up file {filepath}: {str(e)}")
    
    def cleanup_all_temp_files(self):
        """Clean up all temporary files in upload folder"""
        try:
            for filename in os.listdir(self.upload_folder):
                filepath = os.path.join(self.upload_folder, filename)
                if os.path.isfile(filepath):
                    self.cleanup_file(filepath)
                    
            logger.info("All temporary files cleaned up")
            
        except Exception as e:
            logger.error(f"Error during bulk cleanup: {str(e)}")
