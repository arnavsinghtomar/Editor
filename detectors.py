from abc import ABC, abstractmethod
from typing import List, Any, Optional
import pkg_resources
from symspellpy import SymSpell, Verbosity
import language_tool_python
import textstat
import logging

from schemas import DetectionResult, ErrorType, ReadabilityMetrics

logger = logging.getLogger(__name__)

class BaseDetector(ABC):
    @abstractmethod
    def detect(self, text: str, doc: Optional[Any] = None) -> List[DetectionResult]:
        """
        Run detection on the given text/doc.
        """
        pass

class SpellingDetector(BaseDetector):
    def __init__(self):
        # Initialize SymSpell
        self.sym_spell = SymSpell(max_dictionary_edit_distance=2, prefix_length=7)
        
        # Load default dictionary provided by symspellpy
        # Fallback handling might be needed if pkg_resources fails, but it's standard.
        try:
            dictionary_path = pkg_resources.resource_filename(
                "symspellpy", "frequency_dictionary_en_82_765.txt"
            )
            self.sym_spell.load_dictionary(dictionary_path, term_index=0, count_index=1)
        except Exception as e:
            # If resource loading fails, we might need a local fallback or error out
            print(f"Error loading SymSpell dictionary: {e}")
            pass

    def detect(self, text: str, doc: Optional[Any] = None) -> List[DetectionResult]:
        if not doc:
            return []

        results = []
        
        for token in doc:
            # Skip non-alpha, URLs, emails, or Proper Nouns
            if (not token.is_alpha 
                or token.like_url 
                or token.like_email 
                or token.pos_ == "PROPN"
                or token.is_punct):
                continue
            
            word = token.text
            # SymSpell lookup
            suggestions = self.sym_spell.lookup(
                word, 
                Verbosity.CLOSEST, 
                max_edit_distance=2,
                transfer_casing=True
            )
            
            if not suggestions:
                continue

            # Check if the word itself is in the suggestions (exact match)
            # If the best suggestion is the word itself (distance 0), it's correct.
            # But sometimes valid words aren't in the dict. 
            # SymSpell will return the word itself if it's in the dict.
            
            # Simple check: is the word in the dictionary? 
            # Note: valid words might be missing. Over-correction risk.
            
            found_exact = False
            top_suggestions = []
            
            for s in suggestions:
                if s.term.lower() == word.lower():
                    found_exact = True
                top_suggestions.append(s.term)
            
            if found_exact:
                continue
            
            # If not found exact, treat as potential misspelling
            # We take top 3 suggestions
            final_suggestions = top_suggestions[:3]
            
            results.append(DetectionResult(
                error_type=ErrorType.SPELLING,
                message=f"Possible spelling error: '{word}'",
                start_index=token.idx,
                end_index=token.idx + len(word),
                suggestions=final_suggestions,
                confidence=0.9, # High confidence if not in freq dict
                source="symspell"
            ))

        return results

class LanguageToolDetector(BaseDetector):
    def __init__(self):
        # Use public API to avoid 200MB+ download during demo
        # For strict local/privacy usage, remove remote_server argument to download/use local Java server.
        try:
            self.tool = language_tool_python.LanguageTool('en-US', remote_server='https://api.languagetool.org/')
        except Exception as e:
            logger.error(f"Failed to connect to LanguageTool public API: {e}")
            self.tool = None

    def detect(self, text: str, doc: Optional[Any] = None) -> List[DetectionResult]:
        if not self.tool:
            return []
        
        if not text or not text.strip():
            return []
        
        try:
            matches = self.tool.check(text)
        except Exception as e:
            logger.error(f"LanguageTool check failed: {e}")
            return []
        results = []
        for m in matches:
            # Filter out spelling errors if we rely on SymSpell for that 
            # (LT also checks spelling, often better contextually, but prompts wanted SymSpell preferred)
            # We can label them, or rely on aggregation to dedup.
            
            # ErrorType mapping
            # Safely get rule ID
            rule_id = getattr(m, 'ruleId', None)
            if not rule_id and hasattr(m, 'rule'):
                rule_id = m.rule.get('id') if isinstance(m.rule, dict) else getattr(m.rule, 'id', '')
            
            if not rule_id: 
                rule_id = ''
                
            etype = ErrorType.GRAMMAR
            if str(rule_id).startswith('UPPERCASE_SENTENCE_START'):
                etype = ErrorType.STYLE
            elif 'SPELL' in str(rule_id):
                 etype = ErrorType.SPELLING
            
            # Confidence logic (LT doesn't give confidence, we assign medium)
            
            # Safely get length
            length = getattr(m, 'errorLength', None)
            if length is None:
                length = getattr(m, 'length', 0)

            results.append(DetectionResult(
                error_type=etype,
                message=m.message,
                start_index=m.offset,
                end_index=m.offset + length,
                suggestions=m.replacements[:3],
                confidence=0.8,
                source="languagetool"
            ))
        return results

class CustomSpacyGrammarDetector(BaseDetector):
    def detect(self, text: str, doc: Optional[Any] = None) -> List[DetectionResult]:
        if not doc:
            return []
        
        results = []
        for token in doc:
            # Simple Subject-Verb Agreement (rudimentary heuristic)
            if token.dep_ == 'nsubj' and token.head.pos_ == 'VERB':
                subj = token
                verb = token.head
                
                # Check morphology
                subj_num = subj.morph.get("Number")
                verb_num = verb.morph.get("Number")
                verb_pers = verb.morph.get("Person")
                
                # Only check if both have Number features
                if subj_num and verb_num:
                    if subj_num != verb_num:
                        # Edge cases exist (collective nouns, etc.), assign detection check
                        # Exception: "You are" -> You(Singular/Plural) vs Are(Plural) - usually fine.
                        # spaCy morph is decent.
                        
                        # Filter out past tense verbs where agreement is often implicit/same (except was/were)
                        if verb.tag_ == 'VBD' and verb.lemma_ != 'be':
                            continue
                            
                        results.append(DetectionResult(
                            error_type=ErrorType.AGREEMENT,
                            message=f"Possible subject-verb agreement error: '{subj.text}' ({subj_num[0]}) vs '{verb.text}' ({verb_num[0]})",
                            start_index=subj.idx, # highlighting subject or verb? usually highlight verb or relationship
                            end_index=verb.idx + len(verb.text), # span both? or just verb
                            suggestions=[], # Hard to suggest without generating
                            confidence=0.6,
                            source="spacy_rule"
                        ))

            # Determiner-Noun Agreement
            if token.pos_ == 'DET' and token.head.pos_ == 'NOUN':
                det = token
                noun = token.head
                
                det_num = det.morph.get("Number") # e.g. 'This' -> Sing
                noun_num = noun.morph.get("Number") # e.g. 'apples' -> Plur
                
                if det_num and noun_num:
                    # 'This apples' -> mismatch
                    if det_num != noun_num:
                        # exclude some cases? e.g. "The" has no number
                        results.append(DetectionResult(
                            error_type=ErrorType.AGREEMENT,
                            message=f"Determiner agreement error: '{det.text}' ({det_num[0]}) vs '{noun.text}' ({noun_num[0]})",
                            start_index=det.idx,
                            end_index=noun.idx + len(noun.text),
                            suggestions=[],
                            confidence=0.7,
                            source="spacy_rule"
                        ))

        return results

class StyleDetector(BaseDetector):
    def get_readability_metrics(self, text: str) -> ReadabilityMetrics:
        if not text or not text.strip():
            # Return zeros/defaults
            return ReadabilityMetrics(
                flesch_reading_ease=0.0,
                smog_index=0.0,
                flesch_kincaid_grade=0.0,
                coleman_liau_index=0.0,
                automated_readability_index=0.0,
                dale_chall_readability_score=0.0,
                difficult_words=0,
                linsear_write_formula=0.0,
                gunning_fog=0.0,
                text_standard="N/A"
            )
        
        return ReadabilityMetrics(
            flesch_reading_ease=textstat.flesch_reading_ease(text),
            smog_index=textstat.smog_index(text),
            flesch_kincaid_grade=textstat.flesch_kincaid_grade(text),
            coleman_liau_index=textstat.coleman_liau_index(text),
            automated_readability_index=textstat.automated_readability_index(text),
            dale_chall_readability_score=textstat.dale_chall_readability_score(text),
            difficult_words=textstat.difficult_words(text),
            linsear_write_formula=textstat.linsear_write_formula(text),
            gunning_fog=textstat.gunning_fog(text),
            text_standard=str(textstat.text_standard(text))
        )

    def detect(self, text: str, doc: Optional[Any] = None) -> List[DetectionResult]:
        results = []
        if not doc:
            return results

        # 1. Passive Voice Detection (Heuristic: auxpass)
        for token in doc:
            if token.dep_ == "auxpass":
                # The head is usually the main verb
                verb = token.head
                results.append(DetectionResult(
                    error_type=ErrorType.STYLE,
                    message="Passive voice detected. Consider active voice.",
                    start_index=token.idx,
                    end_index=verb.idx + len(verb.text),
                    suggestions=[],
                    confidence=0.6,
                    source="style_heuristic_passive"
                ))

        # 2. Overly long sentences
        for sent in doc.sents:
            if len(sent) > 40: # threshold
                results.append(DetectionResult(
                    error_type=ErrorType.STYLE,
                    message="Sentence is very long (40+ tokens). Consider splitting.",
                    start_index=sent.start_char,
                    end_index=sent.end_char,
                    suggestions=[],
                    confidence=0.5,
                    source="style_heuristic_length"
                ))

        # 3. Wordy constructions (Simple list)
        wordy_map = {
            "in order to": "to",
            "due to the fact that": "because",
            "at this point in time": "now",
            "utilize": "use"
        }
        
        # Simple string search (naive) - for production, use spaCy Matcher
        text_lower = text.lower()
        for phrase, replacement in wordy_map.items():
            start = 0
            while True:
                idx = text_lower.find(phrase, start)
                if idx == -1:
                    break
                results.append(DetectionResult(
                    error_type=ErrorType.STYLE,
                    message=f"Wordy construction '{phrase}'.",
                    start_index=idx,
                    end_index=idx + len(phrase),
                    suggestions=[replacement],
                    confidence=0.8,
                    source="style_heuristic_wordy"
                ))
                start = idx + len(phrase)

        return results
