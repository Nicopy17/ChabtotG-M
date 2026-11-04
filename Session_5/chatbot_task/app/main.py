import streamlit as st
import asyncio
import logging
from dataclasses import dataclass, field

from src.chatbot import CustomChatBot, page_number
import os


@dataclass
class ChatMessage:
    role: str
    content: str
    # Retrieved chunks used for an assistant answer: [{"page": 12, "content": "..."}]
    sources: list = field(default_factory=list)


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


st.session_state["bot"] = load_bot()


def show_sources(sources: list) -> None:
    """Show the retrieved chunks below an answer, so the user can verify where the answer comes from."""
    if not sources:
        return
    with st.expander(f"📚 Sources ({len(sources)})"):
        for i, source in enumerate(sources, start=1):
            st.markdown(f"**[{i}] Page {source['page']}**")
            st.caption(source["content"])


# Initialize session state
if "messages" not in st.session_state:
    st.session_state["messages"] = [ChatMessage(role="assistant", content=WELCOME_MESSAGE)]

if len(st.session_state["messages"]) == 0 or st.sidebar.button("Clear message history"):
    st.session_state["messages"] = [ChatMessage(role="assistant", content=WELCOME_MESSAGE)]

# Display chat messages
for msg in st.session_state.messages:
    with st.chat_message(msg.role):
        st.write(msg.content)
        show_sources(msg.sources)

# Handle user input
if user_query := st.chat_input(placeholder="Ask me anything!"):
    st.session_state.messages.append(ChatMessage(role="user", content=user_query))
    logger.info(f"Write user message in session state {user_query}")
    st.chat_message("user").write(user_query)

    async def handle_user_query(user_query, docs):
        container = st.empty()
        answer = ""
        try:
            async for chunk in st.session_state["bot"].astream(user_query, docs):
                if chunk:
                    answer += chunk
                    container.markdown(answer)
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            container.error("An error occurred while processing your request.")
        return answer

    with st.chat_message("assistant"):
        with st.spinner("Searching for information in your documents and generation response..."):
            docs = st.session_state["bot"].retrieve(user_query)
            sources = [{"page": page_number(doc), "content": doc.page_content} for doc in docs]
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            answer = loop.run_until_complete(handle_user_query(user_query, docs))
        show_sources(sources)

    # Store assistant response in session state
    if answer:
        logger.info(f"Write assistant message in session state {user_query}")
        st.session_state.messages.append(ChatMessage(role="assistant", content=answer, sources=sources))
