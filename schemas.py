from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class ErrorType(str, Enum):
    SPELLING = "spelling"
    GRAMMAR = "grammar"
    AGREEMENT = "agreement"
    PUNCTUATION = "punctuation"
    STYLE = "style"

class DetectionResult(BaseModel):
    error_type: ErrorType
    message: str
    start_index: int
    end_index: int
    suggestions: List[str] = Field(default_factory=list)
    confidence: float = Field(..., ge=0.0, le=1.0)
    source: str  # e.g. "symspell", "languagetool", "spacy_rule"

class ReadabilityMetrics(BaseModel):
    flesch_reading_ease: float
    smog_index: float
    flesch_kincaid_grade: float
    coleman_liau_index: float
    automated_readability_index: float
    dale_chall_readability_score: float
    difficult_words: int
    linsear_write_formula: float
    gunning_fog: float
    text_standard: str

class AnalysisResponse(BaseModel):
    errors: List[DetectionResult]
    readability: ReadabilityMetrics
    llm_used: bool = False
    llm_explanations: Optional[Dict[str, str]] = None 
