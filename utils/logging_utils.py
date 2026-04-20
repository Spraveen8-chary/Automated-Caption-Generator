import json
import logging
from datetime import datetime, timezone


STANDARD_LOG_RECORD_FIELDS = {
    'name',
    'msg',
    'args',
    'levelname',
    'levelno',
    'pathname',
    'filename',
    'module',
    'exc_info',
    'exc_text',
    'stack_info',
    'lineno',
    'funcName',
    'created',
    'msecs',
    'relativeCreated',
    'thread',
    'threadName',
    'processName',
    'process',
    'message',
    'asctime',
}


class StructuredFormatter(logging.Formatter):
    """Emit JSON logs with any extra context attached."""

    def format(self, record):
        payload = {
            'timestamp': datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
        }

        context = {
            key: value
            for key, value in record.__dict__.items()
            if key not in STANDARD_LOG_RECORD_FIELDS and not key.startswith('_')
        }
        if context:
            payload['context'] = context

        if record.exc_info:
            payload['exception'] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=False, default=str)


def configure_logging(app=None, level=None):
    """Configure the root logger once for structured output."""
    root_logger = logging.getLogger()

    if not any(isinstance(handler.formatter, StructuredFormatter) for handler in root_logger.handlers):
        handler = logging.StreamHandler()
        handler.setFormatter(StructuredFormatter())
        root_logger.addHandler(handler)

    if level is None and app is not None:
        level_name = app.config.get('LOG_LEVEL', 'INFO')
        level = getattr(logging, str(level_name).upper(), logging.INFO)
    elif level is None:
        level = logging.INFO

    root_logger.setLevel(level)
    logging.captureWarnings(True)

    if app is not None:
        app.logger.handlers.clear()
        app.logger.propagate = True
        app.logger.setLevel(level)

    return root_logger
