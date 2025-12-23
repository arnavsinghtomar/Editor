import streamlit as st
import time
from pipeline import PipelineManager
from schemas import ErrorType

# Page Config
st.set_page_config(
    page_title="Scribe | AI Proofreader",
    page_icon="✍️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling
st.markdown("""
<style>
    /* Global Styles */
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;700&family=Inter:wght@400;500&display=swap');
    
    body {
        font-family: 'Inter', sans-serif;
        background-color: #fcfcfc;
    }
    
    h1, h2, h3 {
        font-family: 'Outfit', sans-serif;
    }

    /* Main Container */
    .stTextArea textarea {
        font-size: 1.1rem;
        line-height: 1.6;
        border-radius: 8px;
        padding: 1rem;
        border: 1px solid #e2e8f0;
    }
    
    .stTextArea textarea:focus {
        border-color: #6366f1;
        box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2);
    }
    
    /* Highlight Colors */
    .error-highlight {
        padding: 0 2px;
        border-radius: 3px;
        cursor: help;
        transition: background-color 0.2s;
        border-bottom: 2px solid;
        text-decoration: none; 
    }
    
    .error-highlight:hover {
        background-color: rgba(0,0,0,0.05); /* darken slightly on hover */
    }
    
    .spelling-err { background-color: rgba(239, 68, 68, 0.15); border-bottom-color: #ef4444; color: #b91c1c; }
    .grammar-err { background-color: rgba(245, 158, 11, 0.15); border-bottom-color: #f59e0b; color: #b45309; }
    .style-err { background-color: rgba(59, 130, 246, 0.15); border-bottom-color: #3b82f6; color: #1d4ed8; }
    .agreement-err { background-color: rgba(245, 158, 11, 0.15); border-bottom-color: #f59e0b; color: #b45309; }

    /* Document View */
    .document-view {
        background: white;
        padding: 40px;
        border-radius: 8px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
        font-family: 'Inter', sans-serif;
        font-size: 1.05rem;
        line-height: 1.8;
        color: #1e293b;
        white-space: pre-wrap; /* Preserve newlines */
        margin-top: 1rem;
    }

    /* Cards */
    .suggestion-card {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        transition: transform 0.2s;
    }
    
    .suggestion-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border-color: #6366f1;
    }

    /* Badges */
    .st-badge {
        font-size: 0.75rem;
        font-weight: 700;
        padding: 2px 6px;
        border-radius: 4px;
        text-transform: uppercase;
    }
    .bg-spelling { color: #ef4444; background: rgba(239, 68, 68, 0.1); }
    .bg-grammar { color: #f59e0b; background: rgba(245, 158, 11, 0.1); }
    .bg-style { color: #3b82f6; background: rgba(59, 130, 246, 0.1); }
    
    /* Sidebar info */
    .metric-container {
        display: flex;
        justify-content: space-between;
        padding: 10px 0;
        border-bottom: 1px solid #f0f0f0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Pipeline
@st.cache_resource
def load_pipeline():
    return PipelineManager()

pipeline = load_pipeline()

# Header
col1, col2 = st.columns([0.8, 0.2])
with col1:
    st.title("✍️ Scribe")
    st.caption("Advanced Modular Proofreader powered by Python & AI")
with col2:
    st.toggle("Advanced Mode (LLM)", key="use_llm")

# Main Layout
left_col, right_col = st.columns([0.65, 0.35], gap="large")

with left_col:
    st.subheader("Document")
    
    if "input_text" not in st.session_state:
        st.session_state.input_text = "The quick brown fox jump over the lazy dog. Helo world!"

    text_input = st.text_area(
        label="Editor", 
        value=st.session_state.input_text, 
        height=400,
        placeholder="Start typing...",
        key="editor_area",
        label_visibility="collapsed"
    )
    
    c1, c2 = st.columns([0.2, 0.8])
    with c1:
        analyze_btn = st.button("✨ Analyze Text", type="primary", use_container_width=True)
    with c2:
        if text_input:
            words = len(text_input.split())
            st.markdown(f"<div style='text-align:right; color:gray; padding-top:10px'>{words} words</div>", unsafe_allow_html=True)
            
    # Callback for fixing errors
    def apply_fix_callback(err, replacement):
        current = st.session_state.input_text
        # Verify text hasn't changed manually since analysis (simple check)
        # Actually, we rely on user flow.
        prefix = current[:err.start_index]
        suffix = current[err.end_index:]
        new_text = prefix + replacement + suffix
        st.session_state.input_text = new_text
        st.session_state.input_text = new_text
        st.session_state.trigger_analysis = False
        # Clear results as they are now stale
        if "analysis_results" in st.session_state:
            del st.session_state.analysis_results

    # Process Analysis Trigger
    if analyze_btn or st.session_state.get('trigger_analysis', False):
        # Reset trigger immediately
        st.session_state.trigger_analysis = False
        
        with st.spinner("Analyzing..."):
            st.session_state.input_text = text_input
            response = pipeline.analyze(text_input, use_llm=st.session_state.use_llm)
            st.session_state.analysis_results = response

    # Output View for Annotated Text
    if "analysis_results" in st.session_state:
        st.divider()
        st.subheader("Annotated View")
        
        # ... (Annotated view code remains mostly same, just updating rendering logic if needed, but diff is constrained)
        # We need to preserve the annotated view logic but I can't overwrite it all easily.
        # Actually I need to make sure I don't break the lines below.
        # The 'annotated_html' block is large.
        # I will leave the Annotated View block separate if possible, 
        # but I need to update 'render_errors' further down.
        
        # Checking where this block ends... I'm editing lines 150-ish?
        # The user's code snippet for 'annotated view' is lengthy.
        # I will just replace the top block first.
        
        # Function to reconstruct text with highlights
        # Streamlit's annotated_text component is good, but let's manual build HTML for control or use generic logic
        # For simplicity, we just list the errors for now in the sidebar, or attempt a highlight render.
        
        # Simple HTML reconstruction
        results = st.session_state.analysis_results
        original = text_input
        
        # Sort errors reverse to inject tags
        errors = sorted(results.errors, key=lambda x: x.start_index, reverse=True)
        
        annotated_html = original
        
        # Offset tracking is tricky when inserting tags. 
        # We sort by start index DESC so we insert from end to beginning, preventing index shifts.
        errors = sorted(results.errors, key=lambda x: x.start_index, reverse=True)
        
        for e in errors:
            start = e.start_index
            end = e.end_index
            
            # Ensure valid indices
            if start < 0 or end > len(original): continue
            
            cls = "error-highlight"
            if e.error_type == ErrorType.SPELLING: cls += " spelling-err"
            elif e.error_type == ErrorType.GRAMMAR or e.error_type == ErrorType.AGREEMENT: cls += " grammar-err"
            elif e.error_type == ErrorType.STYLE: cls += " style-err"
            
            segment = original[start:end]
            # Escape HTML in segment? Streamlit might handle it, but safer:
            import html
            segment_safe = html.escape(segment)
            tooltip = html.escape(e.message)
            
            replacement = f"<span class='{cls}' title='{tooltip}'>{segment_safe}</span>"
            
            # String splicing
            annotated_html = annotated_html[:start] + replacement + annotated_html[end:]
        
        # Finally, escape the non-highlighted parts? No, because now the whole string is mixed.
        # Wait: if we reconstruct from right to left, we are splicing HTML into raw text.
        # The raw text parts need to be escaped later? No, that's hard.
        # Better: Build from chunks LEFT to RIGHT.
        
        final_html_parts = []
        last_idx = 0
        import html
        
        # Re-sort ASC for left-to-right build
        errors = sorted(results.errors, key=lambda x: x.start_index)
        
        for e in errors:
            start = e.start_index
            end = e.end_index
            
            # Handle non-overlapping text before this error
            if start > last_idx:
                final_html_parts.append(html.escape(original[last_idx:start]))
            
            # Text inside error
            # Check for overlaps? simple pipeline supposed to dedup.
            if start < last_idx: 
                # Overlap detected (shouldn't happen with pipeline logic, but safe guard)
                continue
                
            cls = "error-highlight"
            if e.error_type == ErrorType.SPELLING: cls += " spelling-err"
            elif e.error_type == ErrorType.GRAMMAR or e.error_type == ErrorType.AGREEMENT: cls += " grammar-err"
            elif e.error_type == ErrorType.STYLE: cls += " style-err"
            
            segment = original[start:end]
            tooltip = html.escape(e.message)
            final_html_parts.append(f"<span class='{cls}' title='{tooltip}'>{html.escape(segment)}</span>")
            
            last_idx = end
            
        # Remaining text
        if last_idx < len(original):
            final_html_parts.append(html.escape(original[last_idx:]))
            
        formatted_html = "".join(final_html_parts)
        
        st.markdown(f"<div class='document-view'>{formatted_html}</div>", unsafe_allow_html=True)


with right_col:
    st.subheader("Suggestions")
    
    if "analysis_results" in st.session_state:
        res = st.session_state.analysis_results
        
        # Readability Score
        score = res.readability.flesch_reading_ease
        color = "red"
        if score > 50: color = "orange"
        if score > 70: color = "green"
        
        st.markdown(f"""
        <div style="background:white; padding:15px; border-radius:8px; border:1px solid #eee; margin-bottom:20px; display:flex; justify-content:space-between; align-items:center;">
            <span style="font-weight:600; color:#555">Readability Score</span>
            <span style="font-weight:700; font-size:1.2rem; color:{color}">{int(score)}</span>
        </div>
        """, unsafe_allow_html=True)
        
        # Filter Tabs
        # Streamlit tabs
        tab_all, tab_grammar, tab_spelling, tab_style = st.tabs(["All", "Grammar", "Spelling", "Style"])
        
        def render_errors(error_list, key_prefix="default"):
            if not error_list:
                st.info("No issues found.")
                return

            for i, err in enumerate(error_list):
                # Determine badge style
                badge_cls = "bg-grammar"
                if err.error_type == ErrorType.SPELLING: badge_cls = "bg-spelling"
                elif err.error_type == ErrorType.STYLE: badge_cls = "bg-style"
                
                with st.container():
                    st.markdown(f"""
                    <div class="suggestion-card">
                        <div style="display:flex; justify-content:space-between; margin-bottom:8px">
                            <span class="st-badge {badge_cls}">{err.error_type}</span>
                            <span style="font-size:0.8rem; color:#aaa">Conf: {int(err.confidence*100)}%</span>
                        </div>
                        <div style="margin-bottom:10px; font-size:0.95rem">{err.message}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if err.suggestions:
                        # Display suggestions as non-clickable badges
                        suggs_html = "".join([
                            f'<span style="background:#f1f5f9; color:#334155; padding:4px 8px; border-radius:4px; margin-right:6px; font-size:0.85rem; border:1px solid #e2e8f0; display:inline-block">{s}</span>' 
                            for s in err.suggestions[:3]
                        ])
                        st.markdown(f"<div style='margin-top:8px'>{suggs_html}</div>", unsafe_allow_html=True)

        # Filter logic
        errors = res.errors
        
        with tab_all:
            render_errors(errors, "all")
        with tab_grammar:
            render_errors([e for e in errors if e.error_type in [ErrorType.GRAMMAR, ErrorType.AGREEMENT, ErrorType.PUNCTUATION]], "grammar")
        with tab_spelling:
            render_errors([e for e in errors if e.error_type == ErrorType.SPELLING], "spelling")
        with tab_style:
            render_errors([e for e in errors if e.error_type == ErrorType.STYLE], "style")

    else:
        st.info("Hit 'Analyze' to see suggestions here.")
