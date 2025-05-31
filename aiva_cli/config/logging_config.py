"""Logging configuration for AIVA CLI."""

import logging
import logging.handlers
from pathlib import Path
from datetime import datetime
from typing import Optional
import os


def setup_logging(
    log_level: str = "INFO",
    log_dir: Optional[Path] = None,
    console_output: bool = True,
    file_output: bool = True,
    detailed: bool = False
) -> logging.Logger:
    """Set up logging configuration for AIVA CLI.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory for log files (default: logs/)
        console_output: Enable console output
        file_output: Enable file output
        detailed: Enable detailed logging format
        
    Returns:
        Configured logger instance
    """
    
    # Create logger
    logger = logging.getLogger("aiva_cli")
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Create formatters
    if detailed:
        formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s() - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    else:
        formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    
    # Console handler
    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # File handler
    if file_output:
        if log_dir is None:
            log_dir = Path(__file__).parent.parent / "logs"
        
        # Create logs directory if it doesn't exist
        log_dir.mkdir(exist_ok=True)
        
        # Create timestamped log file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"run_{timestamp}.log"
        
        # Rotating file handler
        file_handler = logging.handlers.RotatingFileHandler(
            filename=log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # Also create a general log file
        general_log = log_dir / "aiva_cli.log"
        general_handler = logging.handlers.RotatingFileHandler(
            filename=general_log,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        general_handler.setFormatter(formatter)
        logger.addHandler(general_handler)
    
    return logger


def get_logger(name: str = "aiva_cli") -> logging.Logger:
    """Get a logger instance.
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def log_function_call(func):
    """Decorator to log function calls.
    
    Args:
        func: Function to decorate
        
    Returns:
        Decorated function
    """
    def wrapper(*args, **kwargs):
        logger = get_logger()
        logger.debug(f"Calling {func.__name__} with args={args}, kwargs={kwargs}")
        try:
            result = func(*args, **kwargs)
            logger.debug(f"{func.__name__} completed successfully")
            return result
        except Exception as e:
            logger.error(f"{func.__name__} failed with error: {str(e)}")
            raise
    return wrapper


def log_performance(func):
    """Decorator to log function performance.
    
    Args:
        func: Function to decorate
        
    Returns:
        Decorated function
    """
    import time
    
    def wrapper(*args, **kwargs):
        logger = get_logger()
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            end_time = time.time()
            duration = end_time - start_time
            logger.info(f"{func.__name__} completed in {duration:.2f} seconds")
            return result
        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time
            logger.error(f"{func.__name__} failed after {duration:.2f} seconds: {str(e)}")
            raise
    
    return wrapper


class ProgressLogger:
    """Logger for tracking progress of long-running operations."""
    
    def __init__(self, total_steps: int, operation_name: str = "Operation"):
        self.total_steps = total_steps
        self.current_step = 0
        self.operation_name = operation_name
        self.logger = get_logger()
        self.start_time = datetime.now()
    
    def step(self, message: str = ""):
        """Log a step completion.
        
        Args:
            message: Optional message for this step
        """
        self.current_step += 1
        progress_percent = (self.current_step / self.total_steps) * 100
        
        elapsed_time = datetime.now() - self.start_time
        
        log_message = f"{self.operation_name} - Step {self.current_step}/{self.total_steps} ({progress_percent:.1f}%)"
        if message:
            log_message += f" - {message}"
        log_message += f" [Elapsed: {elapsed_time}]"
        
        self.logger.info(log_message)
    
    def complete(self, message: str = "Completed successfully"):
        """Log operation completion.
        
        Args:
            message: Completion message
        """
        total_time = datetime.now() - self.start_time
        self.logger.info(f"{self.operation_name} - {message} [Total time: {total_time}]")


# Example usage and testing
if __name__ == "__main__":
    # Test logging setup
    logger = setup_logging(log_level="DEBUG", detailed=True)
    
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    
    # Test progress logger
    progress = ProgressLogger(5, "Test Operation")
    import time
    
    for i in range(5):
        time.sleep(0.1)
        progress.step(f"Processing item {i+1}")
    
    progress.complete()