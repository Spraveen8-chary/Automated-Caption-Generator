import os

from utils.caption_formatter import CaptionFormatter


class ExportService:
    """Generate export artifacts such as SRT files."""

    def __init__(self, upload_folder, caption_formatter=None):
        self.upload_folder = upload_folder
        self.caption_formatter = caption_formatter or CaptionFormatter()

    def build_srt_filename(self, source_filename, style):
        base_name = source_filename.rsplit('.', 1)[0]
        return f"{base_name}_{style}.srt"

    def export_srt(self, captions, source_filename, style):
        srt_filename = self.build_srt_filename(source_filename, style)
        srt_path = os.path.join(self.upload_folder, srt_filename)
        self.caption_formatter.generate_srt(captions, srt_path)
        return {
            'srt_filename': srt_filename,
            'srt_path': srt_path,
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
