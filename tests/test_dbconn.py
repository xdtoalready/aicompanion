import asyncio
import os
import sqlite3
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database.memory_manager import EnhancedMemorySystem, DatabaseMemoryManager
from app.core.ai_client import OptimizedAI

SCHEMA_PATH = Path("app/database/schema.sql")

@pytest.fixture()
def temp_db(tmp_path):
    db_path = tmp_path / "companion.db"
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema_sql = f.read()
    conn = sqlite3.connect(db_path)
    conn.executescript(schema_sql)
    conn.commit()
    conn.close()
    return db_path


def test_database_tables_exist(temp_db):
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = {row[0] for row in cursor.fetchall()}
    required = {'character_profile', 'character_state', 'conversations', 'memories'}
    missing = required - tables
    conn.close()
    assert not missing


@pytest.mark.asyncio
async def test_memory_system_basic(temp_db):
    memory = EnhancedMemorySystem(str(temp_db))
    conv_id = memory.add_conversation(
        "Я люблю читать мангу Токийские мстители",
        ["Ох, отличный выбор!", "Обожаю эту мангу тоже!"],
        "calm",
        "happy",
    )
    assert conv_id is not None
    context = memory.get_context_for_response("манга")
    assert isinstance(context, str) and context
    stats = memory.get_conversation_summary()
    assert stats["recent_conversations"] >= 1


@pytest.mark.asyncio
async def test_database_integration(temp_db):
    db = DatabaseMemoryManager(str(temp_db))
    conv_id = db.save_conversation(
        "Какая манга лучше - Токийские мстители или Атака титанов?",
        [
            "Ох, сложный выбор!",
            "Думаю, Токийские мстители ближе к сердцу.",
            "А тебе какая больше нравится?",
        ],
        "calm",
        "happy",
    )
    assert conv_id is not None
    recent = db.get_recent_conversations(1)
    assert recent
    context = db.build_context_for_prompt("манга аниме")
    assert isinstance(context, str) and context


def test_message_splitting():
    config = {'ai': {'model': 'test', 'max_tokens': 300, 'temperature': 0.8}, 'character': {'name': 'Алиса'}}
    ai = OptimizedAI(None, config)
    examples = [
        ("Привет! || Как дела? || У меня все отлично!", 1),
        ("Ох, интересный вопрос! || Думаю что манга лучше адаптации. || В ней больше деталей!", 3),
        ("Токийские мстители - супер! | Сюжет захватывающий | А какая твоя любимая арка?", 2),
        ("Простое сообщение без разделителей", 1),
    ]
    for text, expected in examples:
        parts = ai._process_raw_response(text)
        assert len(parts) == expected


def test_question_analysis():
    config = {'ai': {'model': 'test', 'max_tokens': 300, 'temperature': 0.8}, 'character': {'name': 'Алиса'}}
    ai = OptimizedAI(None, config)
    cases = [
        ("Что думаешь об адаптации vs манга?", "opinion_question"),
        ("Какая манга лучше?", "comparison_question"),
        ("Токийские мстители или Атака титанов?", "comparison_question"),
        ("Как дела?", "personal_question"),
        ("Сегодня хорошая погода", "statement"),
    ]
    for question, expected in cases:
        assert ai._analyze_question_type(question) == expected

