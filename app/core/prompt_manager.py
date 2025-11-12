"""
Менеджер промптов - централизованное управление шаблонами
"""

import os
import logging
from typing import Dict, Any
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, Template

class PromptManager:
    """Менеджер для загрузки и рендеринга prompt templates"""

    def __init__(self, prompts_dir: str = "prompts"):
        self.logger = logging.getLogger(__name__)

        # Определяем путь к директории промптов
        if os.path.isabs(prompts_dir):
            self.prompts_dir = prompts_dir
        else:
            # Относительно корня проекта
            project_root = Path(__file__).parent.parent.parent
            self.prompts_dir = project_root / prompts_dir

        self.logger.info(f"Prompts directory: {self.prompts_dir}")

        # Инициализируем Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(str(self.prompts_dir)),
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=False
        )

        # Кэш загруженных темплейтов
        self.template_cache = {}

    def render(self, template_name: str, context: Dict[str, Any]) -> str:
        """
        Рендерит промпт из шаблона

        Args:
            template_name: имя файла шаблона (например, "dialogue.jinja2")
            context: словарь с переменными для подстановки

        Returns:
            Отрендеренный промпт
        """
        try:
            # Проверяем кэш
            if template_name not in self.template_cache:
                self.template_cache[template_name] = self.env.get_template(template_name)

            template = self.template_cache[template_name]
            rendered = template.render(context)

            self.logger.debug(f"Rendered template '{template_name}' ({len(rendered)} chars)")
            return rendered

        except Exception as e:
            self.logger.error(f"Error rendering template '{template_name}': {e}")
            raise

    def render_string(self, template_string: str, context: Dict[str, Any]) -> str:
        """
        Рендерит промпт из строки (для динамических промптов)

        Args:
            template_string: строка шаблона
            context: словарь с переменными

        Returns:
            Отрендеренный промпт
        """
        try:
            template = Template(template_string)
            return template.render(context)
        except Exception as e:
            self.logger.error(f"Error rendering string template: {e}")
            raise

    def clear_cache(self):
        """Очищает кэш темплейтов"""
        self.template_cache.clear()
        self.logger.info("Template cache cleared")

    def list_templates(self):
        """Возвращает список доступных темплейтов"""
        try:
            templates = []
            for file in os.listdir(self.prompts_dir):
                if file.endswith(('.jinja2', '.txt', '.md')):
                    templates.append(file)
            return sorted(templates)
        except Exception as e:
            self.logger.error(f"Error listing templates: {e}")
            return []


# Глобальный инстанс (singleton pattern)
_prompt_manager_instance = None

def get_prompt_manager(prompts_dir: str = "prompts") -> PromptManager:
    """Получает глобальный инстанс PromptManager"""
    global _prompt_manager_instance
    if _prompt_manager_instance is None:
        _prompt_manager_instance = PromptManager(prompts_dir)
    return _prompt_manager_instance
