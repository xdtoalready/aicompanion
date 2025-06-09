import asyncio
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.typing_simulator import TypingSimulator

@pytest.fixture(autouse=True)
def fast_sleep(monkeypatch):
    async def _sleep(_):
        pass
    monkeypatch.setattr(asyncio, "sleep", _sleep)


def test_complexity_calculation():
    sim = TypingSimulator()
    text = "Текст с эмодзи! 😊🎉"
    complexity = sim._calculate_complexity_factor(text)
    assert complexity >= 1.0


@pytest.mark.asyncio
async def test_send_messages_with_realistic_timing():
    sim = TypingSimulator()
    messages = ["Привет!", "Как дела?"]
    sent = []

    async def send(msg):
        sent.append(msg)

    await sim.send_messages_with_realistic_timing(messages, send_callback=send)
    assert sent == messages


def test_message_connection():
    sim = TypingSimulator()
    assert sim._are_messages_connected("Привет! Как дела?", "А у меня все отлично!")
    assert not sim._are_messages_connected("Иду в магазин.", "Погода сегодня отличная!")

