import spacy
import subprocess
import sys
import logging

logger = logging.getLogger(__name__)

class SpacyWrapper:
    _nlp = None

    @classmethod
    def get_nlp(cls):
        if cls._nlp is None:
            try:
                cls._nlp = spacy.load("en_core_web_sm")
            except OSError:
                logger.warning("Model 'en_core_web_sm' not found. Attempting download...")
                try:
                    subprocess.check_call([sys.executable, "-m", "spacy", "download", "en_core_web_sm"])
                    cls._nlp = spacy.load("en_core_web_sm")
                except Exception as e:
                    logger.error(f"Failed to download/load 'en_core_web_sm': {e}. Falling back to blank 'en' model.")
                    # Only add sentencizer if not already present (default blank en has nothing)
                    cls._nlp = spacy.blank("en")
                    if "sentencizer" not in cls._nlp.pipe_names:
                        cls._nlp.add_pipe("sentencizer")
        return cls._nlp
