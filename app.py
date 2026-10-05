import streamlit as st
from rag import ask, ingest

st.title("Chatbot")

with st.sidebar:
    st.header("Add PDF")
    f = st.file_uploader("Upload a PDF", type="pdf")
    if f and st.session_state.get("last_pdf") != f.name:
        with open(f.name, "wb") as out:
            out.write(f.getbuffer())
        with st.spinner("Adding PDF..."):
            ingest(f.name)
        st.session_state.last_pdf = f.name
        st.success(f"{f.name} added!")

if "history" not in st.session_state:
    st.session_state.history = []

for role, text, src in st.session_state.history:
    with st.chat_message(role):
        st.write(text)
        if src:
            st.caption("Sources: " + src)

q = st.chat_input("Ask a question")
if q:
    with st.chat_message("user"):
        st.write(q)
    answer, sources = ask(q)
    src = ""
    if "could not find" not in answer.lower():
        unique = sorted({f"{s['file']} (page {s['page']})" for s in sources})
        src = ", ".join(unique)
    with st.chat_message("assistant"):
        st.write(answer)
        if src:
            st.caption("Sources: " + src)
    st.session_state.history += [("user", q, ""), ("assistant", answer, src)]