"""Tests for the SQL database layer. Run from Session_5/chatbot_task/app with: python -m pytest tests"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.database import ChatDatabase  # noqa: E402


def make_db(tmp_path):
    return ChatDatabase(str(tmp_path / "test.db"))


def test_conversation_with_messages_is_persisted(tmp_path):
    db = make_db(tmp_path)
    conversation_id = db.create_conversation("What is supervised learning?")
    db.add_message(conversation_id, "user", "What is supervised learning?")
    db.add_message(conversation_id, "assistant", "Learning with labels.", [{"page": 8, "content": "..."}])

    # A new connection (e.g. after a container restart) still sees the data
    db_after_restart = make_db(tmp_path)
    messages = db_after_restart.get_messages(conversation_id)
    assert [m["role"] for m in messages] == ["user", "assistant"]
    assert messages[1]["sources"] == [{"page": 8, "content": "..."}]
    assert db_after_restart.list_conversations()[0]["title"] == "What is supervised learning?"


def test_conversations_are_listed_newest_first(tmp_path):
    db = make_db(tmp_path)
    first = db.create_conversation("first")
    second = db.create_conversation("second")
    assert [c["id"] for c in db.list_conversations()] == [second, first]


def test_delete_conversation_deletes_messages(tmp_path):
    db = make_db(tmp_path)
    conversation_id = db.create_conversation("chat")
    db.add_message(conversation_id, "user", "hello")
    db.delete_conversation(conversation_id)
    assert db.list_conversations() == []
    assert db.get_messages(conversation_id) == []


def test_feedback_is_saved_updated_and_counted(tmp_path):
    db = make_db(tmp_path)
    conversation_id = db.create_conversation("chat")
    db.add_message(conversation_id, "user", "What is a perceptron?")
    answer_id = db.add_message(conversation_id, "assistant", "A fish.")

    db.set_feedback(answer_id, 1)
    db.set_feedback(answer_id, -1)  # changing the rating replaces it
    assert db.get_messages(conversation_id)[1]["rating"] == -1
    assert db.feedback_stats() == {"positive": 0, "negative": 1}
    assert db.negative_feedback()[0]["question"] == "What is a perceptron?"

    db.set_feedback(answer_id, None)
    assert db.feedback_stats() == {"positive": 0, "negative": 0}
