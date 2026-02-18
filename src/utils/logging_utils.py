import logging
import sys


class ColoredFormatter(logging.Formatter):
    """
    A custom formatter to add colors and make logs more visually distinctive.
    """

    # You can adjust these color codes if you'd like different colors.
    LOG_COLORS = {
        "DEBUG": "\033[94m",  # Blue
        "INFO": "\033[92m",  # Green
        "WARNING": "\033[93m",  # Yellow
        "ERROR": "\033[91m",  # Red
        "CRITICAL": "\033[95m",  # Magenta
    }

    def format(self, record: logging.LogRecord) -> str:
        # Determine which color to use for the current log level.
        log_color = self.LOG_COLORS.get(record.levelname, "\033[0m")

        # Construct a new format string that includes the level name with color
        # and a tab or spacing to ensure alignment.
        # The key is to ensure consistent spacing so that timestamp columns align.
        # You can increase or decrease the width as desired.
        formatter = logging.Formatter(
            fmt=(
                f"{log_color}%(levelname)-8s\033[0m"  # Colored level, left-padded to 8 chars
                "    "  # Fixed tab width or replace with spaces
                "%(asctime)s"  # Timestamp
                " - %(name)s - "  # Logger name
                "%(message)s"  # The actual log message
            ),
            datefmt="%Y-%m-%d %H:%M:%S",  # Date format
        )

        return formatter.format(record)


def create_logger(name: str) -> logging.Logger:
    """
    Create and configure a colored logger that includes level, timestamp, logger name,
    and the message with ANSI color codes for improved visibility.
    """
    logger = logging.getLogger(name)

    # Create a StreamHandler that logs messages to stdout
    stdout = logging.StreamHandler(stream=sys.stdout)

    # Use the custom ColoredFormatter for prettier output with colors and spacing
    colored_formatter = ColoredFormatter()
    stdout.setFormatter(colored_formatter)

    # Add the StreamHandler to the logger
    logger.addHandler(stdout)

    # Set the logger level
    logger.setLevel(logging.WARNING)

    # Disable propagation to prevent duplicate log messages
    logger.propagate = False

    return logger
