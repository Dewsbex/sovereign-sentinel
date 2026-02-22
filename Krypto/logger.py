import logging
import sys
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime

# Ensure logs directory exists
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

# Format for logs
formatter = logging.Formatter(
    fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def setup_logger(name, log_file, level=logging.INFO):
    """Function to setup as many loggers as you want"""
    
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # File Handler
    file_handler = RotatingFileHandler(
        os.path.join(LOG_DIR, log_file), 
        maxBytes=5*1024*1024, # 5MB
        backupCount=5
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Console Handler for real-time feedback
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger

# Create specific loggers
audit_logger = setup_logger('audit_logger', 'audit.log')
trade_logger = setup_logger('trade_logger', 'trades.log')
system_logger = setup_logger('system_logger', 'system.log')

def log_audit(action, details):
    """Log critical audit events like order placement, modification, or cancellation."""
    audit_logger.info(f"AUDIT - Action: {action} - Details: {details}")

def log_trade(symbol, side, price, quantity, status):
    """Log trade executions."""
    trade_logger.info(f"TRADE - {symbol} - {side} - Price: {price} - Qty: {quantity} - Status: {status}")

def log_system(message, level="INFO"):
    """Log system events."""
    if level == "ERROR":
        system_logger.error(message)
    elif level == "WARNING":
        system_logger.warning(message)
    else:
        system_logger.info(message)

if __name__ == "__main__":
    log_system("Logger initialized successfully.")
    log_audit("TEST_AUDIT", "Logger test run.")
    log_trade("BTC/GBP", "BUY", 50000.0, 0.01, "FILLED")
