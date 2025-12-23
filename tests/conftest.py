import pytest
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent

# Test data directory
DATA_DIR = PROJECT_ROOT / "data"
FIXTURES_DIR = Path(__file__).parent / "fixtures"
OUTPUT_DIR = PROJECT_ROOT / "output"


@pytest.fixture
def sample_pdf_path():
    """Path to the DPDP Act sample PDF."""
    return DATA_DIR / "2bf1f0e9f04e6fb4f8fef35e82c42aa5.pdf"


@pytest.fixture
def output_dir():
    """Ensure output directory exists and return path."""
    OUTPUT_DIR.mkdir(exist_ok=True)
    return OUTPUT_DIR


@pytest.fixture
def fixtures_dir():
    """Path to test fixtures directory."""
    FIXTURES_DIR.mkdir(exist_ok=True)
    return FIXTURES_DIR
