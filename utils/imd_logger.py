import os
import sys
import logging
import datetime
from logging.handlers import TimedRotatingFileHandler

_RESET = "\033[0m"
_COLORS = {
    "DEBUG": "\033[36m",
    "INFO": "\033[32m",
    "WARNING": "\033[33m",
    "ERROR": "\033[31m",
    "CRITICAL": "\033[35m",
}

_loggers = {}
_log_dir = ""

class _ColourFormatter(logging.Formatter):
    ICONS = {
        "DEBUG": "[ D ]",
        "INFO": "[OK ]",
        "WARNING": "[WRN]",
        "ERROR": "[ERR]",
        "CRITICAL": "[!!!]",
    }

    def __init__(self, use_colour: bool = True):
        super().__init__()
        self._use_colour = use_colour and _supports_colour()

    def format(self, record: logging.LogRecord) -> str:
        ts = datetime.datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S")
        icon = self.ICONS.get(record.levelname, "     ")
        name = record.name[:12].ljust(12)
        msg = record.getMessage()

        if self._use_colour:
            colour = _COLORS.get(record.levelname, "")
            line = f"  [{ts}]  {colour}{icon}{_RESET}  [{name}]  {msg}"
        else:
            line = f"  [{ts}]  {icon}  [{name}]  {msg}"

        if record.exc_info:
            line = f"{line}\n{self.formatException(record.exc_info)}"
        return line

class _FileFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        ts = datetime.datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S")
        icon = {
            "DEBUG": "[ D ]", "INFO": "[OK ]", "WARNING": "[WRN]",
            "ERROR": "[ERR]", "CRITICAL": "[!!!]"
        }.get(record.levelname, "     ")
        name = record.name[:12].ljust(12)
        msg = record.getMessage()
        line = f"  [{ts}]  {icon}  [{name}]  {msg}"
        if record.exc_info:
            line = f"{line}\n{self.formatException(record.exc_info)}"
        return line

def _supports_colour() -> bool:
    if sys.platform == "win32":
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
            return True
        except Exception:
            return False
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()

def configure_logging(log_dir: str,
                       log_filename: str = "daemon.log",
                       retention_days: int = 14,
                       level: int = logging.DEBUG) -> None:
    global _log_dir
    _log_dir = log_dir
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, log_filename)

    root = logging.getLogger("imd")
    if root.handlers:
        return
    root.setLevel(level)

    fh = TimedRotatingFileHandler(
        filename=log_path,
        when="midnight",
        interval=1,
        backupCount=retention_days,
        encoding="utf-8",
        utc=False,
    )
    fh.setLevel(level)
    fh.setFormatter(_FileFormatter())
    root.addHandler(fh)

    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(level)
    ch.setFormatter(_ColourFormatter(use_colour=True))
    root.addHandler(ch)

    root.info(f"Logging initialised — file: {log_path}  retention: {retention_days}d")

def get_logger(name: str) -> logging.Logger:
    full_name = f"imd.{name}"
    if full_name in _loggers:
        return _loggers[full_name]

    logger = logging.getLogger(full_name)
    root = logging.getLogger("imd")
    if not root.handlers:
        root.setLevel(logging.DEBUG)
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.DEBUG)
        ch.setFormatter(_ColourFormatter(use_colour=True))
        root.addHandler(ch)

    _loggers[full_name] = logger
    return logger

def make_legacy_log_fn(logger: logging.Logger):
    _MAP = {
        "INFO": logger.info,
        "WARN": logger.warning,
        "WARNING": logger.warning,
        "ERROR": logger.error,
        "STEP": logger.info,
        "DAEMON": logger.info,
        "DATA": logger.info,
        "WAIT": logger.info,
    }

    def _log(msg: str, level: str = "INFO") -> None:
        fn = _MAP.get(level.upper(), logger.info)
        fn(msg)

    return _log
