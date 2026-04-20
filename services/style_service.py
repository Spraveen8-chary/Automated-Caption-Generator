from utils.caption_formatter import CaptionFormatter


class StyleService:
    """Apply caption styles to transcript segments."""

    def __init__(self, caption_formatter=None):
        self.caption_formatter = caption_formatter or CaptionFormatter()

    def format(self, transcript, style='meme'):
        return self.caption_formatter.format(transcript, style)

    def format_for_styles(self, transcript, styles):
        return {style: self.format(transcript, style) for style in styles}

    @property
    def styles(self):
        return self.caption_formatter.styles

