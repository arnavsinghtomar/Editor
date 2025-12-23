# ✍️ Scribe | AI Proofreader

A production-ready, modular proofreading system built with Python, Streamlit, and specialized NLP libraries. Scribe combines the speed of rule-based engines with the nuance of Large Language Models (LLMs) to detect grammar, spelling, style, and logical errors.

## ✨ Features

- **Hybrid Detection Engine**:
  - **Grammar & Syntax**: Powered by `LanguageTool` (via public API) and custom `SpaCy` rules.
  - **Spelling**: High-performance correction using `SymSpell`.
  - **Style & Readability**: Readability scoring (Flesch-Kincaid) and heuristic style checks (passive voice, wordiness).
- **Advanced AI Mode**: Optional integration with OpenAI's `gpt-4o-mini` to detect subtle contextual errors, malapropisms, and logical inconsistencies.
- **Interactive UI**: A clean, modern Streamlit interface with inline error highlighting and non-intrusive suggestions.
- **Modular Design**: flattened, easy-to-maintain architecture.

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

### Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/arnavsinghtomar/Editor.git
    cd Editor
    ```

2.  **Install dependencies**:
    ```bash
    uv sync
    # OR if using pip
    pip install -r pyproject.toml # (requires extracting dependencies)
    ```

3.  **Environment Setup**:
    Create a `.env` file in the root directory to enable AI features:
    ```bash
    OPENAI_API_KEY=your_openai_api_key_here
    ```

### Running the App

Start the Streamlit application:

```bash
uv run streamlit run streamlit_app.py
```

The app will open in your browser at `http://localhost:8501`.

## 📂 Project Structure

```
├── streamlit_app.py   # Main UI entry point
├── pipeline.py        # Orchestrates the analysis flow
├── detectors.py       # Core logic for Spelling, Grammar, and Style
├── llm_handler.py     # OpenAI integration for advanced checks
├── spacy_provider.py  # Singleton wrapper for SpaCy model loading
├── schemas.py         # Pydantic models for data validation
├── .env               # API keys (not committed)
└── pyproject.toml     # Dependency management
```

## 🛠️ How It Works

1.  **Normalization**: Text is normalized to Unicode NFC and cleaned.
2.  **Detection**:
    - **SymSpell** scans for typos using a pre-calculated frequency dictionary.
    - **LanguageTool** checks against thousands of grammar rules.
    - **SpaCy** parses the dependency tree to find subject-verb agreement issues.
    - **Style Heuristics** flag passive voice and wordy phrases.
3.  **AI Layer** (Optional): If enabled, the text is sent to GPT-4o-mini to catch "edge cases" like "affect vs effect" in ambiguous contexts.
4.  **Conflict Resolution**: Overlapping errors are deduplicated based on priority (Spelling > Grammar > Style).
5.  **Rendering**: The aggregated results are displayed in the Streamlit UI with color-coded annotations.

## 📝 License

[MIT](LICENSE)
