"""
Движок естественных инициатив - умная система для определения когда персонаж должен написать
"""

import logging
import random
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple


class InitiativeEngine:
    """Умный движок для вычисления вероятности и типа инициативы"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Базовые параметры
        self.base_initiative_chance = 0.3  # 30% базовый шанс каждые 30 минут

    def should_send_initiative(self,
                               character_state: Dict[str, Any],
                               virtual_life_context: Dict[str, Any],
                               last_message_time: Optional[datetime],
                               relationship: Dict[str, Any]) -> Tuple[bool, float, str]:
        """
        Определяет нужно ли отправить инициативу

        Returns:
            (should_send: bool, probability: float, reason: str)
        """

        # Базовая вероятность
        probability = self.base_initiative_chance

        reasons = []

        # 1. Фактор времени с последнего сообщения
        time_factor = self._calculate_time_factor(last_message_time)
        probability *= time_factor
        if time_factor > 1.5:
            reasons.append("долгое молчание")
        elif time_factor < 0.5:
            reasons.append("недавно общались")

        # 2. Фактор настроения
        mood_factor = self._calculate_mood_factor(character_state.get('mood', 'нормальное'))
        probability *= mood_factor
        if mood_factor > 1.2:
            reasons.append("хорошее настроение")
        elif mood_factor < 0.8:
            reasons.append("плохое настроение")

        # 3. Фактор энергии
        energy = character_state.get('energy_level', 70)
        energy_factor = self._calculate_energy_factor(energy)
        probability *= energy_factor
        if energy < 30:
            reasons.append("низкая энергия")

        # 4. Фактор занятости
        activity_factor = self._calculate_activity_factor(virtual_life_context)
        probability *= activity_factor
        if activity_factor < 0.5:
            reasons.append("очень занята")

        # 5. Фактор близости отношений
        intimacy = relationship.get('intimacy_level', 5)
        intimacy_factor = self._calculate_intimacy_factor(intimacy)
        probability *= intimacy_factor
        if intimacy >= 8:
            reasons.append("высокая близость")

        # 6. Фактор времени суток
        time_of_day_factor = self._calculate_time_of_day_factor()
        probability *= time_of_day_factor

        # 7. Фактор дня недели
        day_of_week_factor = self._calculate_day_of_week_factor()
        probability *= day_of_week_factor

        # 8. Контекстные триггеры (бонусная вероятность)
        trigger_bonus = self._check_context_triggers(
            virtual_life_context,
            last_message_time,
            character_state
        )
        probability += trigger_bonus
        if trigger_bonus > 0:
            reasons.append("контекстный триггер")

        # Ограничиваем вероятность
        probability = max(0.0, min(1.0, probability))

        # Решаем отправлять или нет
        should_send = random.random() < probability

        reason_text = ", ".join(reasons) if reasons else "стандартная проверка"

        self.logger.info(
            f"🎲 Инициатива: {should_send} (вероятность: {probability:.2%}, причина: {reason_text})"
        )

        return should_send, probability, reason_text

    def _calculate_time_factor(self, last_message_time: Optional[datetime]) -> float:
        """Фактор времени с последнего сообщения"""
        if not last_message_time:
            return 2.0  # Если никогда не писали - высокий фактор

        time_since = datetime.now() - last_message_time
        hours_since = time_since.total_seconds() / 3600

        # Логика:
        # < 1 час: 0.3x (слишком недавно)
        # 1-2 часа: 0.8x (недавно)
        # 2-4 часа: 1.0x (нормально)
        # 4-8 часов: 1.5x (давно)
        # > 8 часов: 2.0x (очень давно)

        if hours_since < 1:
            return 0.3
        elif hours_since < 2:
            return 0.8
        elif hours_since < 4:
            return 1.0
        elif hours_since < 8:
            return 1.5
        else:
            return 2.0

    def _calculate_mood_factor(self, mood: str) -> float:
        """Фактор настроения"""
        mood_multipliers = {
            'восторженное': 1.5,
            'радостное': 1.3,
            'воодушевленное': 1.4,
            'хорошее': 1.2,
            'игривое': 1.3,
            'нормальное': 1.0,
            'спокойное': 0.9,
            'задумчивое': 0.8,
            'грустное': 0.7,
            'уставшее': 0.6,
            'раздраженное': 0.5,
            'подавленное': 0.4
        }

        return mood_multipliers.get(mood.lower(), 1.0)

    def _calculate_energy_factor(self, energy: int) -> float:
        """Фактор энергии (0-100)"""
        if energy >= 80:
            return 1.3  # Много энергии - активнее
        elif energy >= 60:
            return 1.1
        elif energy >= 40:
            return 1.0
        elif energy >= 20:
            return 0.7
        else:
            return 0.4  # Мало энергии - пассивнее

    def _calculate_activity_factor(self, virtual_life_context: Dict[str, Any]) -> float:
        """Фактор текущей активности"""
        current_activity = virtual_life_context.get('current_activity')

        if not current_activity or current_activity == 'свободна':
            return 1.5  # Свободна - больше шансов написать

        # Проверяем важность текущей активности
        importance = virtual_life_context.get('importance', 5)
        flexibility = virtual_life_context.get('flexibility', 5)

        # Очень важное дело + негибкое = низкий шанс
        if importance >= 8 and flexibility <= 3:
            return 0.3  # Занята критичным делом

        # Важное дело
        if importance >= 7:
            return 0.6

        # Среднее дело
        if importance >= 5:
            return 0.9

        # Неважное дело
        return 1.1

    def _calculate_intimacy_factor(self, intimacy: int) -> float:
        """Фактор близости отношений (0-10)"""
        # Чем ближе отношения - тем чаще пишет
        if intimacy >= 9:
            return 1.8  # Очень близкие - часто пишет
        elif intimacy >= 7:
            return 1.4
        elif intimacy >= 5:
            return 1.0
        elif intimacy >= 3:
            return 0.8
        else:
            return 0.6  # Малознакомы - редко пишет первой

    def _calculate_time_of_day_factor(self) -> float:
        """Фактор времени суток"""
        hour = datetime.now().hour

        # Ночь (00:00 - 06:00): 0.2x (спит)
        if 0 <= hour < 6:
            return 0.2

        # Утро (06:00 - 09:00): 0.8x (просыпается)
        elif 6 <= hour < 9:
            return 0.8

        # День (09:00 - 12:00): 1.2x (активна)
        elif 9 <= hour < 12:
            return 1.2

        # Обед (12:00 - 14:00): 1.0x
        elif 12 <= hour < 14:
            return 1.0

        # День (14:00 - 18:00): 1.3x (самое активное время)
        elif 14 <= hour < 18:
            return 1.3

        # Вечер (18:00 - 21:00): 1.1x (расслабленное время)
        elif 18 <= hour < 21:
            return 1.1

        # Поздний вечер (21:00 - 23:00): 0.9x (устает)
        elif 21 <= hour < 23:
            return 0.9

        # Ночь (23:00 - 00:00): 0.5x (собирается спать)
        else:
            return 0.5

    def _calculate_day_of_week_factor(self) -> float:
        """Фактор дня недели"""
        weekday = datetime.now().weekday()  # 0 = Monday, 6 = Sunday

        # Выходные (суббота, воскресенье): более активна
        if weekday >= 5:
            return 1.2

        # Пятница: тоже активнее
        elif weekday == 4:
            return 1.15

        # Будни: стандартно
        else:
            return 1.0

    def _check_context_triggers(self,
                                virtual_life_context: Dict[str, Any],
                                last_message_time: Optional[datetime],
                                character_state: Dict[str, Any]) -> float:
        """
        Проверяет контекстные триггеры для дополнительной вероятности

        Returns:
            Бонусная вероятность (0.0 - 0.5)
        """
        bonus = 0.0

        # Триггер 1: Только что завершилась активность
        activity_status = virtual_life_context.get('status')
        if activity_status == 'completed':
            bonus += 0.3
            self.logger.debug("🎯 Триггер: активность завершена")

        # Триггер 2: Скоро начнется важная активность (в течение часа)
        next_activity_time = virtual_life_context.get('next_activity_time')
        if next_activity_time:
            time_until = self._parse_time_until(next_activity_time)
            if 0 < time_until <= 60:  # В течение часа
                next_importance = virtual_life_context.get('next_importance', 0)
                if next_importance >= 7:
                    bonus += 0.2
                    self.logger.debug("🎯 Триггер: скоро важное дело")

        # Триггер 3: Давно не общались + высокая близость
        if last_message_time:
            hours_since = (datetime.now() - last_message_time).total_seconds() / 3600
            intimacy = character_state.get('intimacy', 5)

            if hours_since > 12 and intimacy >= 7:
                bonus += 0.25
                self.logger.debug("🎯 Триггер: скучает")

        # Триггер 4: Особое настроение (очень хорошее или очень плохое)
        mood = character_state.get('mood', '').lower()
        if mood in ['восторженное', 'радостное', 'воодушевленное']:
            bonus += 0.15
            self.logger.debug("🎯 Триггер: отличное настроение")
        elif mood in ['грустное', 'подавленное']:
            bonus += 0.2
            self.logger.debug("🎯 Триггер: нужна поддержка")

        return min(bonus, 0.5)  # Максимум +50% вероятности

    def _parse_time_until(self, time_str: str) -> int:
        """Парсит строку времени и возвращает минут до него"""
        try:
            # Формат: "17:00"
            target_hour, target_minute = map(int, time_str.split(':'))
            now = datetime.now()
            target = now.replace(hour=target_hour, minute=target_minute, second=0)

            if target < now:
                # Если время уже прошло сегодня, берем завтра
                target += timedelta(days=1)

            delta = target - now
            return int(delta.total_seconds() / 60)

        except Exception:
            return 999  # Не смогли распарсить

    def get_initiative_topic(self,
                            virtual_life_context: Dict[str, Any],
                            character_state: Dict[str, Any],
                            recent_topics: list) -> str:
        """
        Выбирает тему для инициативы на основе контекста

        Args:
            virtual_life_context: текущая виртуальная жизнь
            character_state: состояние персонажа
            recent_topics: последние темы инициатив (чтобы не повторяться)

        Returns:
            Тема для инициативы
        """

        current_activity = virtual_life_context.get('current_activity', '')
        activity_type = virtual_life_context.get('activity_type', '')
        mood = character_state.get('mood', 'нормальное')

        topics = []

        # Темы на основе текущей активности
        if current_activity and current_activity != 'свободна':
            topics.append(f"поделиться процессом: {current_activity}")
            topics.append(f"рассказать о сложностях с: {current_activity}")
            topics.append(f"попросить совет по: {current_activity}")

        # Темы на основе типа активности
        if 'cosplay' in activity_type:
            topics.extend([
                "рассказать о новом косплее",
                "показать прогресс в работе над костюмом",
                "поделиться идеей для косплея"
            ])
        elif 'hobby' in activity_type:
            topics.append("поделиться увлечением")
        elif 'social' in activity_type:
            topics.append("рассказать о встрече с друзьями")

        # Темы на основе настроения
        if mood in ['восторженное', 'радостное', 'воодушевленное']:
            topics.extend([
                "поделиться радостной новостью",
                "рассказать что вдохновило"
            ])
        elif mood in ['грустное', 'подавленное']:
            topics.extend([
                "поделиться переживаниями",
                "попросить поддержки"
            ])

        # Общие темы
        topics.extend([
            "поинтересоваться делами",
            "рассказать о дне",
            "предложить совместную активность",
            "вспомнить общий момент"
        ])

        # Фильтруем недавние темы
        filtered_topics = [t for t in topics if t not in recent_topics[-3:]]

        # Если все темы были недавно, используем любую
        if not filtered_topics:
            filtered_topics = topics

        return random.choice(filtered_topics)
