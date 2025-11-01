"""
Logging-Konfiguration
"""

import logging
import sys
from pathlib import Path
from datetime import datetime


def setup_logging(log_dir: Path) -> None:
    """
    Richtet Logging ein
    
    Args:
        log_dir: Verzeichnis für Log-Dateien
    """
    
    # Log-Datei
    log_file = log_dir / "app.log"
    
    # Formatter
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # File-Handler
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    
    # Console-Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    # Root-Logger konfigurieren
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Begrüßungsmeldung
    logging.info("=" * 60)
    logging.info("ABC-CO₂-Bilanzierer gestartet")
    logging.info(f"Log-Datei: {log_file}")
    logging.info("=" * 60)
