# Modular Proofreading System

A production-ready, modular proofreading system in Python, featuring spell checking, grammar rule usage, styling heuristics, and an optional LLM fallback.

## Architecture

The system converts text into structured feedback through a multi-stage pipeline:

1.  **Normalization**: Unicode NFC and whitespace handling.
2.  **Segmentation**: Tokenization/Parsing via spaCy.
3.  **Detectors**:
    *   **Spelling**: SymSpell (fast, dictionary-based).
    *   **Grammar**: LanguageTool (via `language-tool-python`) + Custom spaCy rules (Agreement).
    *   **Style**: Readability metrics (textstat) + Heuristics (Passive voice, Wordy phrases).
4.  **LLM Layer** (Optional): GPT-4o-mini for edge cases, explanations, and rewrites.
5.  **Aggregation**: Conflict resolution and confidence scoring.

## Setup

1.  **Install Dependencies**:
    This project uses `uv` for dependency management, but standard pip works too.
    ```bash
    pip install spacy symspellpy language-tool-python textstat pydantic fastapi uvicorn openai python-dotenv pytest
    # or
    uv sync
    ```

2.  **Environment Variables**:
    Create a `.env` file for LLM functionality:
    ```
    OPENAI_API_KEY=your_key_here
    ```

3.  **Run the API**:
    ```bash
    python main.py
    ```
    The API will be available at `http://localhost:8000`.
    Docs at: `http://localhost:8000/docs`.

## Usage

**Analyze Text**:
POST `/api/v1/analyze`
```json
{
  "text": "The quick brown fox jump over the lazy dog.",
  "use_llm": false
}
```

**Explain Error**:
POST `/api/v1/explain`

**Rewrite Text**:
POST `/api/v1/rewrite`

## Project Structure

- `app/core`: Configuration, Normalization, SpaCy wrapper.
- `app/detectors`: Logic for Spelling, Grammar, Style.
- `app/pipeline`: Orchestration and Conflict Resolution.
- `app/llm`: OpenAI integration.
- `app/api`: FastAPI routes.
- `app/models`: Pydantic Schemas.

## Testing

Run the test suite:
```bash
pytest tests/
```
