__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import streamlit as st
import trulens.dashboard.streamlit as trulens_st
from trulens.core import TruSession

from base import rag, filtered_rag, tru_rag, filtered_tru_rag

st.set_page_config(
    page_title="Use TruLens in Streamlit",
    page_icon="🦑",
)

st.title("TruLens ❤️ Streamlit")

st.write("Learn about the Pacific Northwest, and view tracing & evaluation metrics powered by TruLens 🦑.")

tru = TruSession()

with_filters = st.toggle("Use Context Filter Guardrails", value=False)

def generate_response(input_text):
    if with_filters:
        app = filtered_tru_rag
        with filtered_tru_rag as recording:
            response = filtered_rag.query(input_text)
    else:
        app = tru_rag
        with tru_rag as recording:
            response = rag.query(input_text)

    record = recording.get()
    
    return record, response

with st.form("my_form"):
    text = st.text_area(
        "Enter text:", "When was the University of Washington founded?"
    )
    submitted = st.form_submit_button("Submit")
    if submitted:
        record, response = generate_response(text)
        st.info(response)

if submitted:
    with st.expander("See the trace of this record 👀"):
        trulens_st.trulens_trace(record=record)

    trulens_st.trulens_feedback(record=record)

