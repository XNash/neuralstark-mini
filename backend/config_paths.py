"""
Cross-platform path configuration for NeuralStark.
Automatically detects project root and sets up cache directories.
Works on Windows, Linux, and macOS.
"""
import os
import warnings
from pathlib import Path

# Suppress FutureWarning about TRANSFORMERS_CACHE deprecation
# We use HF_HOME which is the recommended approach for transformers v5+
warnings.filterwarnings('ignore', category=FutureWarning, module='transformers.utils.hub')

# Get project root (two levels up from this file: backend -> app)
PROJECT_ROOT = Path(__file__).parent.parent.resolve()

# Define cache directories relative to project root
CACHE_DIR = PROJECT_ROOT / ".cache"
HF_CACHE = CACHE_DIR / "huggingface"
ST_CACHE = CACHE_DIR / "sentence_transformers"
CHROMA_DIR = PROJECT_ROOT / "chroma_db"
FILES_DIR = PROJECT_ROOT / "files"

# Ensure directories exist
CACHE_DIR.mkdir(parents=True, exist_ok=True)
HF_CACHE.mkdir(parents=True, exist_ok=True)
ST_CACHE.mkdir(parents=True, exist_ok=True)
CHROMA_DIR.mkdir(parents=True, exist_ok=True)
FILES_DIR.mkdir(parents=True, exist_ok=True)

# Set environment variables for HuggingFace and related libraries
# These must be set before importing transformers/sentence_transformers
os.environ['HF_HOME'] = str(HF_CACHE)
# Note: TRANSFORMERS_CACHE is deprecated in favor of HF_HOME (v5+)
os.environ['SENTENCE_TRANSFORMERS_HOME'] = str(ST_CACHE)

# Export as strings for compatibility
HF_CACHE_STR = str(HF_CACHE)
ST_CACHE_STR = str(ST_CACHE)
CHROMA_DIR_STR = str(CHROMA_DIR)
FILES_DIR_STR = str(FILES_DIR)
PROJECT_ROOT_STR = str(PROJECT_ROOT)

# Print configuration for debugging
print(f"[Config] Project Root: {PROJECT_ROOT_STR}")
print(f"[Config] HF Cache: {HF_CACHE_STR}")
print(f"[Config] Chroma DB: {CHROMA_DIR_STR}")
print(f"[Config] Files Directory: {FILES_DIR_STR}")
print(f"[Config] Platform: {os.name}")
