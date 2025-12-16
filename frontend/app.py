# Streamlit app - to be filled from streamlit_app_py.txt
import streamlit as st
import httpx
import json
from datetime import datetime
from typing import Optional, Dict, Any
import time

# Page configuration
st.set_page_config(
    page_title="GitHub Issue Analyzer",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply custom CSS
st.markdown("""
<style>
    .main {
        padding: 2rem;
    }
    .stButton > button {
        width: 100%;
        height: 2.5rem;
        font-size: 1rem;
    }
    .result-container {
        border-left: 5px solid #1f77e2;
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f0f4f8;
    }
    .priority-critical {
        color: #d62728;
        font-weight: bold;
    }
    .priority-high {
        color: #ff7f0e;
        font-weight: bold;
    }
    .priority-medium {
        color: #2ca02c;
        font-weight: bold;
    }
    .priority-low {
        color: #1f77e2;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "api_url" not in st.session_state:
    st.session_state.api_url = "http://localhost:8000"
if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None
if "is_loading" not in st.session_state:
    st.session_state.is_loading = False


def get_priority_color(score: int) -> str:
    """Get CSS class for priority color."""
    if score >= 4:
        return "priority-critical"
    elif score == 3:
        return "priority-high"
    elif score == 2:
        return "priority-medium"
    else:
        return "priority-low"


def call_backend_api(
    github_url: str,
    issue_number: int,
    use_cache: bool = True
) -> Optional[Dict[str, Any]]:
    """Call the backend API for issue analysis."""
    try:
        with httpx.Client(timeout=60.0) as client:
            response = client.post(
                f"{st.session_state.api_url}/api/v1/analyze",
                json={
                    "github_url": github_url,
                    "issue_number": issue_number,
                    "use_cache": use_cache
                }
            )
            response.raise_for_status()
            return response.json()
    except httpx.ConnectError:
        st.error(
            "❌ Cannot connect to backend API. "
            "Make sure the FastAPI server is running on http://localhost:8000"
        )
        return None
    except httpx.HTTPStatusError as e:
        error_detail = e.response.json().get("detail", str(e))
        st.error(f"❌ API Error: {error_detail}")
        return None
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        return None


def display_analysis_result(result: Dict[str, Any]) -> None:
    """Display the analysis result in a formatted way."""
    if not result.get("success"):
        st.error(f"Analysis failed: {result.get('error', 'Unknown error')}")
        return

    data = result.get("data", {})
    metadata = result.get("metadata", {})

    # Main result container
    col1, col2 = st.columns([3, 1])

    with col1:
        st.markdown("### 📊 Analysis Results")

        # Summary
        st.markdown(f"""
        **Summary:** {data.get('summary', 'N/A')}
        """)

        # Type and Priority in columns
        type_col, priority_col = st.columns(2)

        with type_col:
            issue_type = data.get("type", "unknown").upper()
            st.markdown(f"**Issue Type:** `{issue_type}`")

        with priority_col:
            priority_score = data.get("priority_score", {})
            score = priority_score.get("score", 0)
            priority_class = get_priority_color(score)
            st.markdown(f"**Priority:** <span class='{priority_class}'>{score}/5</span>", unsafe_allow_html=True)

        # Priority Justification
        st.markdown(f"""
        **Justification:** {priority_score.get('justification', 'N/A')}
        """)

        # Suggested Labels
        labels = data.get("suggested_labels", [])
        if labels:
            st.markdown("**Suggested Labels:**")
            label_cols = st.columns(len(labels))
            for i, label in enumerate(labels):
                with label_cols[i]:
                    st.markdown(f"🏷️ `{label}`")

        # Potential Impact
        st.markdown(f"""
        **Potential Impact:** {data.get('potential_impact', 'N/A')}
        """)

    with col2:
        st.markdown("### ⏱️ Metadata")
        if metadata:
            st.metric(
                "Analysis Time",
                f"{metadata.get('analysis_time_ms', 'N/A')} ms"
            )
            cached = "✓ Yes" if metadata.get('cached') else "✗ No"
            st.metric("From Cache", cached)

            if metadata.get('existing_labels'):
                st.markdown("**Existing Labels:**")
                for label in metadata['existing_labels']:
                    st.caption(label)

    # GitHub Issue Link
    if metadata.get('issue_url'):
        st.markdown(f"""
        ---
        [🔗 View on GitHub]({metadata['issue_url']})
        """)


def main():
    """Main Streamlit application."""
    # Header
    st.title("🔍 GitHub Issue Analyzer")
    st.markdown("""
    Analyze GitHub issues with AI-powered insights powered by Google Gemini.
    Get intelligent summaries, priority scores, and suggested labels instantly.
    """)

    # Sidebar Configuration
    with st.sidebar:
        st.markdown("### ⚙️ Configuration")

        # Backend URL
        backend_url = st.text_input(
            "Backend API URL",
            value=st.session_state.api_url,
            placeholder="http://localhost:8000"
        )
        st.session_state.api_url = backend_url

        # Check backend health
        if st.button("🏥 Check Backend Health"):
            try:
                with httpx.Client(timeout=5.0) as client:
                    response = client.get(f"{backend_url}/api/v1/health")
                    if response.status_code == 200:
                        st.success("✓ Backend is healthy!")
                    else:
                        st.error(f"Backend returned status {response.status_code}")
            except Exception as e:
                st.error(f"Cannot connect to backend: {str(e)}")

        st.divider()

        # Statistics
        if st.button("📊 View API Statistics"):
            try:
                with httpx.Client(timeout=5.0) as client:
                    response = client.get(f"{backend_url}/api/v1/stats")
                    if response.status_code == 200:
                        stats = response.json()
                        st.metric("Total Analyses", stats.get("total_analyses", 0))
                        st.metric("Cache Hit Rate", f"{stats.get('cache_hit_rate', 0):.1f}%")
                        st.metric("Avg Response Time", f"{stats.get('avg_response_time_ms', 0):.0f} ms")
            except Exception as e:
                st.warning(f"Could not fetch statistics: {str(e)}")

        st.divider()

        # Documentation
        with st.expander("📚 Help & Documentation"):
            st.markdown("""
            ### How to use:
            1. Enter a GitHub repository URL (e.g., https://github.com/facebook/react)
            2. Enter the issue number you want to analyze
            3. Click "Analyze Issue" to get instant insights
            
            ### Features:
            - **Summary**: One-sentence issue summary
            - **Type Classification**: bug, feature_request, documentation, question, other
            - **Priority Scoring**: 1-5 score with justification
            - **Label Suggestions**: Recommended GitHub labels
            - **Impact Analysis**: Potential impact assessment
            
            ### Powered by:
            - **Backend**: FastAPI with async/await
            - **LLM**: Google Gemini Pro
            - **Caching**: Redis (optional) / In-Memory
            """)

    # Main content area
    st.markdown("### 🚀 Analyze an Issue")

    # Input form
    col1, col2 = st.columns([3, 1])

    with col1:
        github_url = st.text_input(
            "GitHub Repository URL",
            placeholder="https://github.com/facebook/react",
            help="Enter the full GitHub repository URL"
        )

    with col2:
        issue_number = st.number_input(
            "Issue Number",
            min_value=1,
            value=1,
            help="Enter the GitHub issue number"
        )

    # Use cache checkbox
    use_cache = st.checkbox("Use cached results if available", value=True)

    # Analyze button
    if st.button("🔍 Analyze Issue", use_container_width=True):
        if not github_url or not issue_number:
            st.error("Please fill in all fields")
        else:
            with st.spinner("🔄 Analyzing issue..."):
                result = call_backend_api(github_url, int(issue_number), use_cache)
                if result:
                    st.session_state.analysis_result = result
                    st.success("✓ Analysis complete!")

    # Display results
    if st.session_state.analysis_result:
        st.divider()
        display_analysis_result(st.session_state.analysis_result)

        # Export options
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("📋 Copy as JSON"):
                st.code(
                    json.dumps(st.session_state.analysis_result, indent=2),
                    language="json"
                )

        with col2:
            # Download as JSON
            json_str = json.dumps(st.session_state.analysis_result, indent=2)
            st.download_button(
                label="⬇️ Download JSON",
                data=json_str,
                file_name=f"analysis_{int(time.time())}.json",
                mime="application/json"
            )

        with col3:
            if st.button("🔄 Clear Results"):
                st.session_state.analysis_result = None
                st.rerun()


if __name__ == "__main__":
    main()