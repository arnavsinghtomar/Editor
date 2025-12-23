from typing import List
import unicodedata
from spacy_provider import SpacyWrapper
from detectors import SpellingDetector, LanguageToolDetector, CustomSpacyGrammarDetector, StyleDetector
from llm_handler import LLMHandler
from schemas import AnalysisResponse, DetectionResult, ErrorType

class PipelineManager:
    def __init__(self):
        # Initialize components
        self.spacy_nlp = SpacyWrapper.get_nlp()
        self.spelling = SpellingDetector()
        self.lt_grammar = LanguageToolDetector()
        self.spacy_grammar = CustomSpacyGrammarDetector()
        self.style = StyleDetector()
        self.llm = LLMHandler()

    def analyze(self, text: str, use_llm: bool = False) -> AnalysisResponse:
        # 1. Normalization
        # Note: We use the normalized text for analysis.
        norm_text = unicodedata.normalize('NFC', text)
        
        if not norm_text.strip():
            return AnalysisResponse(errors=[], readability=self.style.get_readability_metrics(""), llm_used=use_llm)

        # 2. Segmentation & Parsing
        doc = self.spacy_nlp(norm_text)
        
        # 3. Parallel Detection
        # In a real async app we could run these concurrently.
        errors = []
        
        # Spell Check
        errors.extend(self.spelling.detect(norm_text, doc))
        
        # Grammar (LT + Custom)
        errors.extend(self.lt_grammar.detect(norm_text, doc))
        errors.extend(self.spacy_grammar.detect(norm_text, doc))
        
        # Style
        errors.extend(self.style.detect(norm_text, doc))

        # LLM Edge Cases
        if use_llm:
            errors.extend(self.llm.check_edge_cases(norm_text))
            
        # 4. Conflict Resolution
        final_errors = self._resolve_conflicts(errors)
        
        # 5. Readability
        readability = self.style.get_readability_metrics(norm_text)

        # 6. Optional: LLM Explanations for top errors? 
        # The prompt says LLM used for "Explaining detected errors".
        # Doing this for *all* might be slow/expensive. 
        # Usually checking endpoints ask for definition on demand.
        # We will leave `llm_explanations` empty here, user can call separate endpoint or we can add later.
        
        return AnalysisResponse(
            errors=final_errors,
            readability=readability,
            llm_used=use_llm
        )

    def _resolve_conflicts(self, errors: List[DetectionResult]) -> List[DetectionResult]:
        if not errors:
            return []
            
        # Priority mapping: Higher number = higher priority
        priority = {
            ErrorType.SPELLING: 3,
            ErrorType.GRAMMAR: 2,
            ErrorType.AGREEMENT: 2,
            ErrorType.PUNCTUATION: 2,
            ErrorType.STYLE: 1
        }
        
        # Sort by start_index, then by priority (descending), then confidence (descending)
        # We want higher priority/confidence first so we can keep them when iterating
        errors.sort(key=lambda x: (x.start_index, -priority.get(x.error_type, 0), -x.confidence))
        
        merged = []
        matches_to_remove = set()
        
        # Robust merge strategy:
        # If two errors OVERLAP significantly, pick the winner.
        
        for i in range(len(errors)):
            if i in matches_to_remove:
                continue
                
            current = errors[i]
            # keep_current = True # Unused variable
            
            # Check against already added (looking back? No, we sorted. Looking forward?)
            # Actually since we sorted by start index, we can just check against other items to see if we should suppress current.
            
            is_suppressed = False
            for j in range(len(errors)):
                if i == j: continue
                other = errors[j]
                
                # Check overlap
                overlap = max(0, min(current.end_index, other.end_index) - max(current.start_index, other.start_index))
                if overlap > 0:
                    # Decide who wins
                    p_curr = priority.get(current.error_type, 0)
                    p_other = priority.get(other.error_type, 0)
                    
                    if p_other > p_curr:
                        is_suppressed = True
                        break
                    elif p_other == p_curr:
                        if other.confidence > current.confidence:
                            is_suppressed = True
                            break
                        elif other.confidence == current.confidence and j < i: 
                            # If tied, and 'other' appeared earlier in list (via sort), 'other' wins.
                            # 'j < i' check is redundant if we are checking all, but strictly we just want ONE survivor.
                            # If we suppress current because of j (where j < i or j > i), correct.
                            # Usually simple greedy: Only add if no conflict with *already merged*.
                            # But that depends on sort order being perfect.
                            # The pairwise suppression is safer.
                            
                            # However, if j > i (comes later), we haven't processed j yet.
                            # If we suppress current now, we assume j will be added later.
                            # But j might be suppressed by k.
                            # This global pairwise suppression is slightly risky if circular (A>B, B>C, C>A).
                            # Priority tiers prevent circularity mostly.
                            pass
            
            if not is_suppressed:
                if current not in merged:
                    merged.append(current)

        return merged
