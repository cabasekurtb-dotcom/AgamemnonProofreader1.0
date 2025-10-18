import streamlit as st
import google.generativeai as genai
import json
import re
import html

# ---- SETUP ----
st.set_page_config(
    page_title="Agamemnon Proofreader",
    page_icon="https://github.com/cabasekurtb-dotcom/AgamemnonProofreader/blob/main/openart-image_qep0Q1ob_1760730245491_raw.png?raw=true",
    layout="wide"
)

st.title("Agamemnon Proofreader")
st.caption("Property of Kurt 'Isko' Cabase")

# ---- LOAD API KEY ----
API_KEY = st.secrets["general"]["GEMINI_API_KEY"]
genai.configure(api_key=API_KEY)
MODEL_NAME = "models/gemini-2.5-flash"

# ---- SESSION STATE ----
if "results" not in st.session_state:
    st.session_state.results = []
if "proofread_done" not in st.session_state:
    st.session_state.proofread_done = False
if "text_input" not in st.session_state:
    st.session_state.text_input = ""
if "applied_edits" not in st.session_state:
    st.session_state.applied_edits = {}

# ---- UPLOAD TEXT FILE ----
uploaded_file = st.file_uploader("Upload your .txt file", type="txt")
if uploaded_file:
    st.session_state.text_input = uploaded_file.read().decode("utf-8")

# ---- PROOFREAD FUNCTION ----
def proofread_text(text):
    model = genai.GenerativeModel(MODEL_NAME)
    prompt = f"""
    You are a professional proofreader. 
    Return ONLY valid JSON with this structure:
    [
      {{
        "original": "...",
        "corrected": "...",
        "reason": "..."
      }}
    ]
    Text:
    {text}
    """
    response = model.generate_content(prompt)
    raw = response.text.strip()

    match = re.search(r'\[.*\]', raw, re.S)
    if match:
        raw = match.group(0)
    try:
        return json.loads(raw)
    except:
        return []

# ---- TEXT AREA ----
st.session_state.text_input = st.text_area(
    "Story or passage:",
    value=st.session_state.text_input,
    height=300
)

# ---- BUTTONS ----
col1, col2, col3 = st.columns([1,1,1])

with col1:
    if st.button("Proofread"):
        if not st.session_state.text_input.strip():
            st.warning("Please enter some text first!")
        else:
            with st.spinner("Analyzing text..."):
                st.session_state.results = proofread_text(st.session_state.text_input)
                if st.session_state.results:
                    st.success("Proofreading complete!")
                    st.session_state.proofread_done = True
                    st.session_state.applied_edits = {i: None for i in range(len(st.session_state.results))}
                else:
                    st.error("No corrections found or model returned invalid data.")

with col2:
    if st.button("Clear Highlights"):
        st.session_state.text_input = ""
        st.session_state.results = []
        st.session_state.proofread_done = False
        st.session_state.applied_edits = {}

with col3:
    if st.button("Download Final Text"):
        final_text = st.session_state.text_input
        for idx, decision in st.session_state.applied_edits.items():
            if decision == "accept":
                final_text = final_text.replace(
                    st.session_state.results[idx]["original"],
                    st.session_state.results[idx]["corrected"]
                )
        st.download_button(
            label="Download as .txt",
            data=final_text,
            file_name="proofread_result.txt",
            mime="text/plain"
        )

# ---- DISPLAY HIGHLIGHTS WITH ACCEPT/REJECT ----
if st.session_state.proofread_done:
    highlighted_text = st.session_state.text_input
    for idx, edit in enumerate(st.session_state.results):
        escaped_original = re.escape(edit["original"])
        tooltip_safe = html.escape(edit["reason"].replace("\n", " "))

        # Display Accept/Reject buttons for this edit
        col_a, col_b = st.columns([1,1])
        with col_a:
            if st.button(f"Accept: {edit['original']}", key=f"accept_{idx}"):
                st.session_state.applied_edits[idx] = "accept"
        with col_b:
            if st.button(f"Reject: {edit['original']}", key=f"reject_{idx}"):
                st.session_state.applied_edits[idx] = "reject"

        # Highlight (still shows regardless of Accept/Reject until final download)
        replacement = f"<span style='background-color:#ffeb3b;' title='{tooltip_safe}'>{edit['original']}</span>"
        highlighted_text = re.sub(escaped_original, replacement, highlighted_text)

    highlighted_text = highlighted_text.replace("\n", "<br>")
    st.markdown("### Highlights with Tooltips")
    st.markdown(highlighted_text, unsafe_allow_html=True)
