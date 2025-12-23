import os
import json
from typing import List, Optional
from openai import OpenAI
from dotenv import load_dotenv
from schemas import DetectionResult, ErrorType

load_dotenv()

class LLMHandler:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.client = None
        self.available = False
        if self.api_key:
            try:
                self.client = OpenAI(api_key=self.api_key)
                self.available = True
            except Exception as e:
                print(f"Failed to initialize OpenAI client: {e}")

    def explain_error(self, error: DetectionResult, context: str) -> str:
        """
        Explain a specific error in simple language using LLM.
        """
        if not self.available:
            return "Explanation unavailable (LLM not configured)."

        prompt = f"""
        Explain the following grammar/spelling error to a user in simple terms.
        Error Message: "{error.message}"
        Context: "{context}"
        Offending Text: "{context[error.start_index:error.end_index] if len(context) > error.end_index else 'unknown'}"
        keep it brief (1 sentence).
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful proofreading assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=60
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Error generating explanation: {str(e)}"

    def check_edge_cases(self, text: str) -> List[DetectionResult]:
        """
        Use LLM to find contextual ambiguity or subtle errors not caught by rules.
        """
        if not self.available:
            return []

        prompt = """
        Analyze the following text for subtle contextual grammar errors, malapropisms, or logical inconsistencies in phrasing.
        Do NOT report style issues, spelling, or basic grammar (rules cover those).
        Focus on things like:
        - "There" vs "Their" if valid in POS but wrong in context (though rules might catch this).
        - "Affect" vs "Effect".
        - Wrong distinct word usage (e.g. "for all intensive purposes").
        
        Return JSON format:
        {
            "errors": [
                {"message": "...", "start_index": 0, "end_index": 5, "suggestion": "..."}
            ]
        }
        Recalculate indices carefully based on the provided text.
        If no errors, return {"errors": []}.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a strict proofreader. Output valid JSON only."},
                    {"role": "user", "content": f"{prompt}\n\nText: {text}"}
                ],
                response_format={"type": "json_object"},
                temperature=0.0
            )
            data = json.loads(response.choices[0].message.content)
            results = []
            for item in data.get("errors", []):
                # We trust LLM indices, but should validate them?
                # For now, simplistic mapping.
                results.append(DetectionResult(
                    error_type=ErrorType.GRAMMAR, # Logic/Context falls under grammar approx
                    message=item.get("message"),
                    start_index=item.get("start_index"),
                    end_index=item.get("end_index"),
                    suggestions=[item.get("suggestion")] if item.get("suggestion") else [],
                    confidence=0.7,
                    source="llm_edge_case"
                ))
            return results
        except Exception as e:
            print(f"LLM Edge case check failed: {e}")
            return []

    def rewrite_text(self, text: str) -> str:
        if not self.available:
            return "Rewrite unavailable."
            
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert editor. Improve clarity and flow. Maintain original meaning."},
                    {"role": "user", "content": f"Rewrite this text:\n{text}"}
                ]
            )
            return response.choices[0].message.content.strip()
        except Exception:
            return "Rewrite failed."
