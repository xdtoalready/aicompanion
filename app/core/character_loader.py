# Система загрузки и управления персонажами (ИСПРАВЛЕНО)

import json
import os
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime


class CharacterLoader:
    """Загрузчик и менеджер персонажей"""

    def __init__(self, characters_dir: str = "characters", config_dir: str = "config"):
        self.characters_dir = Path(characters_dir)
        self.config_dir = Path(config_dir)
        self.logger = logging.getLogger(__name__)

        # Создаем директории если их нет
        self.characters_dir.mkdir(exist_ok=True)
        self.config_dir.mkdir(exist_ok=True)

        self.current_character = None
        self.relationship_history = {}

        self._load_current_character()
        self._load_relationship_history()

    # ... (остальные методы остаются без изменений) ...
    
    def get_available_characters(self) -> List[Dict[str, str]]:
        """Возвращает список доступных персонажей"""
        characters = []

        for char_file in self.characters_dir.glob("*.json"):
            try:
                with open(char_file, "r", encoding="utf-8") as f:
                    char_data = json.load(f)

                characters.append(
                    {
                        "id": char_file.stem,
                        "name": char_data.get("name", "Неизвестно"),
                        "description": char_data.get(
                            "short_description", "Описание недоступно"
                        ),
                        "file": str(char_file),
                    }
                )
            except Exception as e:
                self.logger.error(f"Ошибка загрузки персонажа {char_file}: {e}")

        return characters

    def load_character(
        self,
        character_id: Optional[str] = None,
        profile_path: Optional[str] = None,
        profile_data: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Загружает персонажа"""

        if profile_data is not None:
            character_data = profile_data
            if character_id is None:
                character_id = character_data.get("id", "custom_character")
        else:
            if profile_path:
                char_file = Path(profile_path)
            else:
                if character_id is None:
                    self.logger.error("Не указан character_id")
                    return None
                char_file = self.characters_dir / f"{character_id}.json"

            if not char_file.exists():
                self.logger.error(f"Файл персонажа не найден: {char_file}")
                return None

            try:
                with open(char_file, "r", encoding="utf-8") as f:
                    character_data = json.load(f)
            except Exception as e:
                self.logger.error(f"Ошибка загрузки персонажа {char_file}: {e}")
                return None

            if character_id is None:
                character_id = character_data.get("id", char_file.stem)

        # Загружаем историю отношений для этого персонажа
        if character_id in self.relationship_history:
            character_data["current_relationship"] = self.relationship_history[
                character_id
            ]
        else:
            character_data["current_relationship"] = self._create_new_relationship(
                character_data
            )
            self.relationship_history[character_id] = character_data[
                "current_relationship"
            ]
            self._save_relationship_history()

        self.current_character = character_data
        self._save_current_character(character_id)

        self.logger.info(
            f"Персонаж загружен: {character_data.get('name', character_id)}"
        )
        return character_data

    def switch_character(self, new_character_id: str) -> bool:
        """Переключение на другого персонажа"""
        # Сохраняем текущее состояние отношений
        if self.current_character:
            current_id = self.current_character.get("id", "unknown")
            if current_id in self.relationship_history:
                self.relationship_history[current_id] = self.current_character.get(
                    "current_relationship", {}
                )

        # Загружаем нового персонажа
        new_character = self.load_character(new_character_id)
        if new_character:
            self._save_relationship_history()
            self.logger.info(f"Переключение на персонажа: {new_character.get('name')}")
            return True

        return False

    def get_current_character(self) -> Optional[Dict[str, Any]]:
        """Возвращает текущего персонажа"""
        return self.current_character

    def update_relationship_progress(self, updates: Dict[str, Any]):
        """Обновляет прогресс отношений"""
        if not self.current_character:
            return

        current_rel = self.current_character.get("current_relationship", {})
        current_rel.update(updates)
        current_rel["last_updated"] = datetime.now().isoformat()

        # Сохраняем изменения
        character_id = self.current_character.get("id", "unknown")
        self.relationship_history[character_id] = current_rel
        self.current_character["current_relationship"] = current_rel

        self._save_relationship_history()
        self.logger.info(f"Отношения обновлены: {updates}")

    def get_character_context_for_ai(self) -> str:
        """Генерирует контекст персонажа для AI промптов"""
        if not self.current_character:
            return "Персонаж не загружен"

        char = self.current_character
        rel = char.get("current_relationship", {})

        # Базовая информация
        context_parts = [
            f"ПЕРСОНАЖ: {char.get('name', 'Неизвестно')}",
            f"Возраст: {char.get('age', 'Неизвестно')}",
            f"Описание: {char.get('personality', {}).get('description', '')}",
        ]

        # Черты характера
        if char.get("personality", {}).get("key_traits"):
            traits = char["personality"]["key_traits"][:5]  # Первые 5
            context_parts.append(f"Черты: {', '.join(traits)}")

        # Текущие отношения
        context_parts.append(f"\nОТНОШЕНИЯ:")
        context_parts.append(f"Тип: {rel.get('type', 'неопределенные')}")
        context_parts.append(f"Стадия: {rel.get('stage', 'начальная')}")
        context_parts.append(f"Уровень близости: {rel.get('intimacy_level', 1)}/10")

        # Предыстория
        if rel.get("backstory"):
            context_parts.append(f"Предыстория: {rel['backstory']}")

        # Текущее состояние отношений
        if rel.get("current_dynamic"):
            context_parts.append(f"Текущая динамика: {rel['current_dynamic']}")

        # Особенности речи
        if char.get("speech"):
            speech = char["speech"]
            context_parts.append(f"\nРЕЧЬ:")
            context_parts.append(f"Стиль: {speech.get('style', '')}")
            if speech.get("catchphrases"):
                context_parts.append(
                    f"Фразочки: {', '.join(speech['catchphrases'][:3])}"
                )

        # Интересы и хобби
        if char.get("interests"):
            interests = char["interests"][:4]  # Первые 4
            context_parts.append(f"\nИНТЕРЕСЫ: {', '.join(interests)}")

        return "\n".join(context_parts)

    def _create_new_relationship(
        self, character_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Создает новую историю отношений"""
        default_relationship = character_data.get("default_relationship", {})

        return {
            "type": default_relationship.get("type", "friends"),
            "stage": default_relationship.get("initial_stage", "знакомство"),
            "intimacy_level": default_relationship.get("initial_intimacy", 1),
            "backstory": default_relationship.get("backstory", ""),
            "current_dynamic": default_relationship.get("current_dynamic", ""),
            "relationship_events": [],
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
        }

    def _load_current_character(self):
        """Загружает текущего персонажа"""
        current_file = self.config_dir / "current_character.json"

        if current_file.exists():
            try:
                with open(current_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                character_id = data.get("character_id")
                if character_id:
                    self.load_character(character_id)
            except Exception as e:
                self.logger.error(f"Ошибка загрузки текущего персонажа: {e}")

    def _save_current_character(self, character_id: str):
        """Сохраняет ID текущего персонажа"""
        current_file = self.config_dir / "current_character.json"

        try:
            with open(current_file, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "character_id": character_id,
                        "switched_at": datetime.now().isoformat(),
                    },
                    f,
                    ensure_ascii=False,
                    indent=2,
                )
        except Exception as e:
            self.logger.error(f"Ошибка сохранения текущего персонажа: {e}")

    def _load_relationship_history(self):
        """Загружает историю отношений"""
        history_file = self.config_dir / "relationship_history.json"

        if history_file.exists():
            try:
                with open(history_file, "r", encoding="utf-8") as f:
                    self.relationship_history = json.load(f)
            except Exception as e:
                self.logger.error(f"Ошибка загрузки истории отношений: {e}")
                self.relationship_history = {}
        else:
            self.relationship_history = {}

    def _save_relationship_history(self):
        """Сохраняет историю отношений"""
        history_file = self.config_dir / "relationship_history.json"

        try:
            with open(history_file, "w", encoding="utf-8") as f:
                json.dump(self.relationship_history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"Ошибка сохранения истории отношений: {e}")


# ИСПРАВЛЕНО: Используем паттерн Singleton вместо глобальной переменной
_character_loader_instance = None

def get_character_loader() -> CharacterLoader:
    """Получает единственный экземпляр CharacterLoader"""
    global _character_loader_instance
    if _character_loader_instance is None:
        _character_loader_instance = CharacterLoader()
    return _character_loader_instance