import streamlit as st
import asyncio
import logging
import re
from dataclasses import dataclass, field

from src.chatbot import CustomChatBot, page_number
from src.database import ChatDatabase
import os


@dataclass
class ChatMessage:
    role: str
    content: str
    # Retrieved chunks used for an assistant answer: [{"page": 12, "content": "..."}]
    sources: list = field(default_factory=list)
    # Primary key of the message in the SQL database (None for the welcome message)
    id: int | None = None
    # Feedback of the user: 1 = 👍, -1 = 👎, None = not rated
    rating: int | None = None


INDEX_DATA = os.environ.get("INDEX_DATA", "0")
PULL_EMBEDDING_MODEL = os.environ.get("PULL_EMBEDDING_MODEL", "0")
WELCOME_MESSAGE = "How can I help you?"

# Configure logger
logging.basicConfig(
    level=logging.INFO,  # Change to DEBUG for more details
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),  # Console logs
    ],
)

logger = logging.getLogger(__name__)

# Streamlit UI setup
st.set_page_config(page_title="ChatDoc", page_icon="📄")
st.header("Chat with your Document")


@st.cache_resource(show_spinner="Loading models and preparing the knowledge base (the first start can take several minutes)...")
def load_bot() -> CustomChatBot:
    # cache_resource creates the bot only once per server process and shares it between all browser tabs.
    # Otherwise every new tab would pull the models and (with INDEX_DATA=1) rebuild the index again.
    return CustomChatBot(index_data=bool(int(INDEX_DATA)), pull_embedding_model=bool(int(PULL_EMBEDDING_MODEL)))


@st.cache_resource
def load_db() -> ChatDatabase:
    return ChatDatabase()


st.session_state["bot"] = load_bot()
db = load_db()


def plain_text(text: str) -> str:
    """Show PDF text as it is: collapse whitespace (indentation would become a code block) and escape markdown characters."""
    text = re.sub(r"\s+", " ", text).strip()
    return re.sub(r"([\\`*_{}\[\]()#+\-.!|>~<$])", r"\\\1", text)


def show_sources(sources: list) -> None:
    """Show the retrieved chunks below an answer, so the user can verify where the answer comes from."""
    if not sources:
        return
    with st.expander(f"📚 Sources ({len(sources)})"):
        for i, source in enumerate(sources, start=1):
            st.markdown(f"**[{i}] Page {source['page']}**")
            st.caption(plain_text(source["content"]))


def save_feedback(message_id: int) -> None:
    # st.feedback("thumbs") returns 1 for 👍, 0 for 👎 and None if the selection was removed
    value = st.session_state[f"feedback_{message_id}"]
    rating = None if value is None else (1 if value == 1 else -1)
    db.set_feedback(message_id, rating)
    logger.info(f"Saved feedback {rating} for message {message_id}")


def show_feedback(msg: "ChatMessage") -> None:
    """👍/👎 below every stored answer, the rating is saved in the SQL database."""
    if msg.role != "assistant" or msg.id is None:
        return
    key = f"feedback_{msg.id}"
    if key not in st.session_state:
        st.session_state[key] = None if msg.rating is None else (1 if msg.rating == 1 else 0)
    st.feedback("thumbs", key=key, on_change=save_feedback, args=(msg.id,))


# ---------- Sidebar: conversations stored in the SQL database ----------

if "conversation_id" not in st.session_state:
    # None = new chat, it is written to the database with the first question
    st.session_state["conversation_id"] = None

st.sidebar.title("💬 Chats")
if st.sidebar.button("➕ New chat", use_container_width=True):
    st.session_state["conversation_id"] = None

conversations = db.list_conversations()
if conversations:
    ids = [c["id"] for c in conversations]
    titles = {c["id"]: c["title"] for c in conversations}
    current = st.session_state["conversation_id"]
    selected = st.sidebar.radio(
        "Previous chats",
        options=ids,
        index=ids.index(current) if current in ids else None,
        format_func=lambda conversation_id: titles[conversation_id],
    )
    if selected is not None and selected != current:
        st.session_state["conversation_id"] = selected
        st.rerun()

    if st.session_state["conversation_id"] is not None and st.sidebar.button("🗑️ Delete this chat", use_container_width=True):
        db.delete_conversation(st.session_state["conversation_id"])
        st.session_state["conversation_id"] = None
        st.rerun()

stats = db.feedback_stats()
st.sidebar.divider()
st.sidebar.subheader("⭐ Feedback")
col_positive, col_negative = st.sidebar.columns(2)
col_positive.metric("👍 Helpful", stats["positive"])
col_negative.metric("👎 Not helpful", stats["negative"])
negative = db.negative_feedback(limit=5)
if negative:
    with st.sidebar.expander("Last answers rated 👎"):
        for item in negative:
            st.markdown(f"**Q:** {item['question']}")
            st.caption(item["answer"])

# ---------- Chat ----------

conversation_id = st.session_state["conversation_id"]
messages = [ChatMessage(role="assistant", content=WELCOME_MESSAGE)]
if conversation_id is not None:
    messages += [ChatMessage(role=m["role"], content=m["content"], sources=m["sources"], id=m["id"], rating=m["rating"]) for m in db.get_messages(conversation_id)]

# Display chat messages
for msg in messages:
    with st.chat_message(msg.role):
        st.write(msg.content)
        show_sources(msg.sources)
        show_feedback(msg)

# Handle user input
if user_query := st.chat_input(placeholder="Ask me anything!"):
    # Chat history without the welcome message, as (role, content)
    history = [(m.role, m.content) for m in messages if m.id is not None]

    if conversation_id is None:
        title = user_query if len(user_query) <= 40 else user_query[:40] + "..."
        conversation_id = db.create_conversation(title)
        st.session_state["conversation_id"] = conversation_id

    db.add_message(conversation_id, "user", user_query)
    logger.info(f"Saved user message in conversation {conversation_id}: {user_query}")
    st.chat_message("user").write(user_query)

    async def handle_user_query(user_query, docs, history):
        container = st.empty()
        answer = ""
        try:
            async for chunk in st.session_state["bot"].astream(user_query, docs, history):
                if chunk:
                    answer += chunk
                    container.markdown(answer)
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            container.error("An error occurred while processing your request.")
        return answer

    with st.chat_message("assistant"):
        with st.spinner("Searching for information in your documents and generation response..."):
            docs = st.session_state["bot"].retrieve(user_query, history)
            sources = [{"page": page_number(doc), "content": doc.page_content} for doc in docs]
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            answer = loop.run_until_complete(handle_user_query(user_query, docs, history))
        show_sources(sources)

    # Store assistant response in the database
    if answer:
        db.add_message(conversation_id, "assistant", answer, sources)
        logger.info(f"Saved assistant message in conversation {conversation_id}")

    # Rerun so the new chat appears in the sidebar
    st.rerun()
