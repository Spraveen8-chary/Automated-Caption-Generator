import os
import logging

from moviepy.editor import VideoFileClip

from utils.caption_formatter import CaptionFormatter

logger = logging.getLogger(__name__)


class ExportService:
    """Generate export artifacts such as SRT files."""

    def __init__(self, output_folder, caption_formatter=None):
        self.output_folder = output_folder
        self.upload_folder = output_folder
        os.makedirs(self.output_folder, exist_ok=True)
        self.caption_formatter = caption_formatter or CaptionFormatter()

    def build_srt_filename(self, source_filename, style, language=None):
        base_name = source_filename.rsplit('.', 1)[0]
        if language:
            return f"{base_name}_{style}_{language}.srt"
        return f"{base_name}_{style}.srt"

    def build_burned_video_filename(self, source_filename, style, language=None):
        base_name = source_filename.rsplit('.', 1)[0]
        if language:
            return f"{base_name}_{style}_{language}_captions.mp4"
        return f"{base_name}_{style}_captions.mp4"

    def export_srt(self, captions, source_filename, style, language=None):
        srt_filename = self.build_srt_filename(source_filename, style, language=language)
        srt_path = os.path.join(self.output_folder, srt_filename)
        self.caption_formatter.generate_srt(captions, srt_path)
        return {
            'srt_filename': srt_filename,
            'srt_path': srt_path,
        }

    @staticmethod
    def _escape_subtitles_path(path):
        """Escape a local path for ffmpeg's subtitles filter."""
        normalized_path = os.path.abspath(path).replace('\\', '/')
        if ':' in normalized_path[:3]:
            normalized_path = normalized_path.replace(':', '\\:', 1)
        normalized_path = normalized_path.replace("'", "\\'")
        return normalized_path

    def export_burned_video(self, source_video_path, srt_path, source_filename, style, language=None):
        if not os.path.exists(source_video_path):
            raise FileNotFoundError(f'Source video not found: {source_video_path}')

        if not os.path.exists(srt_path):
            raise FileNotFoundError(f'SRT file not found: {srt_path}')

        burned_video_filename = self.build_burned_video_filename(source_filename, style, language=language)
        burned_video_path = os.path.join(self.output_folder, burned_video_filename)
        subtitles_filter = f"subtitles='{self._escape_subtitles_path(srt_path)}'"

        clip = VideoFileClip(source_video_path)
        try:
            clip.write_videofile(
                burned_video_path,
                codec='libx264',
                audio_codec='aac',
                temp_audiofile=f"{burned_video_path}.temp-audio.m4a",
                remove_temp=True,
                ffmpeg_params=['-vf', subtitles_filter],
                logger=None,
            )
        finally:
            clip.close()

        logger.info(
            "burned.video.exported",
            extra={
                'source_video_path': source_video_path,
                'burned_video_path': burned_video_path,
            },
        )
        return {
            'burned_video_filename': burned_video_filename,
            'burned_video_path': burned_video_path,
        }

    def export_style_map(self, style_map, source_filename):
        results = []

        for style, captions in style_map.items():
            export_data = self.export_srt(captions, source_filename, style)
            results.append({
                'style': style,
                'srt_filename': export_data['srt_filename'],
                'captions': captions[:10],
                'total_captions': len(captions),
            })

        return results
