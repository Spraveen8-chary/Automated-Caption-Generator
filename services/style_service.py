import json
import logging
import os
import re

from google import genai
from google.genai import types

from utils.caption_formatter import CaptionFormatter

logger = logging.getLogger(__name__)


class GeminiCaptionStyler:
    """Rewrite transcript segments into a requested caption style with Gemini."""

    provider_name = 'gemini'

    def __init__(self, api_key, model_name=None):
        if not api_key:
            raise ValueError('GOOGLE_API_KEY is required for Gemini caption styling')

        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name or os.getenv('GEMINI_MODEL', 'gemini-2.5-flash')

    @staticmethod
    def _strip_code_fences(text):
        cleaned = (text or '').strip()
        cleaned = cleaned.removeprefix('```json').removeprefix('```').strip()
        if cleaned.endswith('```'):
            cleaned = cleaned[:-3].strip()
        return cleaned

    @staticmethod
    def _parse_response(response_text, source_segments):
        cleaned = GeminiCaptionStyler._strip_code_fences(response_text)
        candidates = [cleaned]

        if cleaned and cleaned[0] not in '[{':
            match = re.search(r'(\[[\s\S]*\]|\{[\s\S]*\})', cleaned)
            if match:
                candidates.insert(0, match.group(1))

        parsed = None
        for candidate in candidates:
            try:
                parsed = json.loads(candidate)
                break
            except json.JSONDecodeError:
                continue

        if parsed is None:
            raise ValueError('Gemini style response was not valid JSON')

        if isinstance(parsed, dict):
            captions = parsed.get('captions') or parsed.get('segments') or parsed.get('results') or []
        else:
            captions = parsed

        if not isinstance(captions, list):
            raise ValueError('Gemini style response must contain a list of captions')

        normalized = []
        for index, caption in enumerate(captions):
            source_segment = source_segments[min(index, len(source_segments) - 1)]
            if not isinstance(caption, dict):
                caption = {'text': str(caption)}

            start = float(caption.get('start', source_segment.get('start', 0.0)))
            end = float(caption.get('end', source_segment.get('end', start)))
            text = caption.get('text', '').strip()
            if not text:
                text = str(source_segment.get('text', '')).strip()

            normalized.append({
                'start': start,
                'end': end,
                'text': text,
            })

        if not normalized:
            raise ValueError('Gemini style response did not produce any captions')

        return normalized

    def format(self, transcript, style='meme'):
        segments = transcript.get('segments', [])
        if not segments:
            return []

        prompt = self._build_prompt(transcript, style)
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=[
                types.Content(
                    role='user',
                    parts=[types.Part.from_text(text=prompt)],
                )
            ],
        )
        return self._parse_response(getattr(response, 'text', ''), segments)

    @staticmethod
    def _build_prompt(transcript, style):
        segments_json = json.dumps(transcript.get('segments', []), ensure_ascii=False)
        return (
            "Rewrite the transcript captions into the requested caption style.\n"
            f"Style: {style}\n"
            "Rules:\n"
            "- Keep the same language as the input.\n"
            "- Do not translate.\n"
            "- Preserve the same number of caption entries.\n"
            "- Preserve the start and end timestamps for each caption.\n"
            "- Only rewrite the caption text to match the style.\n"
            "- Return only valid JSON.\n"
            "Output format:\n"
            '{"captions":[{"start":0.0,"end":1.0,"text":"..."}]}\n'
            f"Input segments:\n{segments_json}"
        )


class StyleService:
    """Apply caption styles to transcript segments."""

    def __init__(self, caption_formatter=None, gemini_api_key=None, gemini_model=None):
        self.caption_formatter = caption_formatter or CaptionFormatter()
        self.gemini_styler = None
        if gemini_api_key:
            try:
                self.gemini_styler = GeminiCaptionStyler(gemini_api_key, model_name=gemini_model)
            except Exception as error:
                logger.warning("style.gemini.disabled", extra={'error': str(error)})

    def format(self, transcript, style='meme'):
        if self.gemini_styler is not None:
            try:
                return self.gemini_styler.format(transcript, style)
            except Exception as error:
                logger.warning(
                    "style.gemini.fallback",
                    extra={'style': style, 'error': str(error)},
                )
        return self.caption_formatter.format(transcript, style)

    def format_for_styles(self, transcript, styles):
        return {style: self.format(transcript, style) for style in styles}

    def preview_styles(self, transcript, styles):
        style_map = self.format_for_styles(transcript, styles)
        previews = []

        for style, captions in style_map.items():
            previews.append({
                'style': style,
                'captions': captions[:5],
                'total_captions': len(captions),
            })

        return previews

    @property
    def styles(self):
        return self.caption_formatter.styles
