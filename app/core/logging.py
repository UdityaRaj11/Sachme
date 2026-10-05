import sys
import logging
import json
from datetime import datetime

class JsonFormatter(logging.Formatter):
    """Formats log records as JSON objects for structured log collectors."""
    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "timestamp": datetime.utcfromtimestamp(record.created).isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "line": record.lineno,
        }
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_obj)


def setup_logging(debug: bool = False) -> logging.Logger:
    """Configures structured logging for the application."""
    log_level = logging.DEBUG if debug else logging.INFO
    root_logger = logging.getLogger("truth_firewall")
    root_logger.setLevel(log_level)
    
    # Avoid duplicate handlers on re-init
    if not root_logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(log_level)
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] [%(name)s:%(lineno)d]: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        root_logger.addHandler(handler)
        
    return root_logger

# Module level logger
logger = setup_logging()
