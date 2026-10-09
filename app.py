"""Staff-facing web app:  streamlit run app.py"""

import time

import streamlit as st

from src.config import INDEX_DIR, USE_EMBEDDINGS
from src.feedback import log_feedback, summary
from src.generate import answer
from src.ingest import build_index
from src.retrieve import Retriever

st.set_page_config(page_title="Hotel Ops Assistant", page_icon="🛎️")


@st.cache_resource
def get_retriever():
    # The index isn't committed to git, so build it on first start (e.g. on Streamlit Cloud).
    if not (INDEX_DIR / "chunks.json").exists():
        with st.spinner("Building the search index (first start only)..."):
            build_index(use_embeddings=USE_EMBEDDINGS)
    return Retriever(use_embeddings=USE_EMBEDDINGS)


retriever = get_retriever()

st.title("🛎️ Hotel Operations Knowledge Assistant")
st.caption("Answers come only from the hotel's own documents, with sources.")

prop = st.sidebar.selectbox("Your property", retriever.properties())
st.sidebar.markdown(
    "**Try asking:**\n"
    "- Can a guest bring a dog?\n"
    "- How late can a Gold member check out on Saturday?\n"
    "- How much is airport pickup?"
)
stats = summary()
if stats["total"]:
    st.sidebar.caption(f"Staff feedback: {stats['helpful']}/{stats['total']} helpful ({stats['rate']:.0%})")

question = st.text_input("Ask a policy question", placeholder="Can a guest bring a dog?")

# Keep the latest answer in session state so clicking a feedback button doesn't re-ask the question.
key = (prop, question.strip())
if question.strip() and st.session_state.get("key") != key:
    start = time.time()
    with st.spinner("Searching documents..."):
        hits = retriever.search(question, prop)
        result = answer(question, prop, hits)
    st.session_state.update(key=key, hits=hits, result=result, elapsed=time.time() - start, rated=False)

if question.strip() and st.session_state.get("key") == key:
    result, hits = st.session_state["result"], st.session_state["hits"]
    (st.success if result["found"] else st.warning)(result["answer"])
    usage = result["usage"]
    st.caption(
        f"{st.session_state['elapsed']:.1f}s · {usage['input_tokens']} input / {usage['output_tokens']} output tokens"
    )

    if st.session_state["rated"]:
        st.caption("Thanks, your feedback was saved.")
    else:
        col1, col2, _ = st.columns([1, 1, 4])
        if col1.button("👍 Helpful"):
            log_feedback(question, prop, result, helpful=True)
            st.session_state["rated"] = True
            st.rerun()
        if col2.button("👎 Not helpful"):
            log_feedback(question, prop, result, helpful=False)
            st.session_state["rated"] = True
            st.rerun()

    with st.expander("Sources used"):
        for c in result["citations"]:
            st.markdown(f"**[{c['n']}] {c['source']}** › {c['section']}")
            st.text(c["text"])
    with st.expander("Debug: everything retrieved"):
        for c in hits:
            st.markdown(f"`{c['score']}` **{c['source']}** › {c['section']}")
