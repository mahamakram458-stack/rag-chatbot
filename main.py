import streamlit as st
from rag import ingest, ask

st.set_page_config(page_title="PDF Q&A Assistant", page_icon="📄")
st.title("📄 RAG Document Q&A")

up = st.file_uploader("PDF upload karein", type="pdf")
if up is not None:
    with open(up.name, "wb") as f:
        f.write(up.getbuffer())
    if st.session_state.get("last") != up.name:
        with st.spinner("PDF padh raha hoon..."):
            ingest(up.name)
        st.session_state["last"] = up.name
        st.success(f"{up.name} ready")

q = st.text_input("Apna sawal likhein")
if q:
    with st.spinner("Jawab dhoondh raha hoon..."):
        answer, sources = ask(q)
    st.write(answer)
    pages = sorted({f"{s['file']} (page {s['page']})" for s in sources})
    st.caption("Sources: " + ", ".join(pages))