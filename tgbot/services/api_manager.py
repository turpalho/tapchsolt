from typing import Any, AsyncGenerator
import requests
import logging
import asyncio

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessage
from langchain_google_genai import ChatGoogleGenerativeAI

logger = logging.getLogger(__name__)


class OpenaiClient:
    def __init__(self, api_key: str, system_message: str):
        self.client: ChatOpenAI = ChatOpenAI(model="gpt-3.5-turbo")
        self.async_client: AsyncOpenAI = AsyncOpenAI(api_key=api_key)
        self.system_message = system_message

    async def async_get_response(self, messages: list):

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    self.system_message,
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )

        chain = prompt | self.client

        completion = await chain.ainvoke(
            {"messages": messages, }
        )
        return completion

    # # TODO create async openai client
    # async def async_get_response(self, messages: list) -> ChatCompletionMessage:
    #     completion = await self.async_client.chat.completions.create(
    #         model='gpt-3.5-turbo',
    #         messages=messages
    #     )
    #     return completion.choices[0].message


class GoogleClient:
    def __init__(self, api_key: str, system_message: str):
        self.client: ChatGoogleGenerativeAI = ChatGoogleGenerativeAI(
            api_key=api_key,
            # model="gemini-2.5-pro",
            model="gemini-2.5-flash",
            temperature=1,
            max_tokens=512,
            timeout=None,
            max_retries=2,
            # Пробуем включить thinking mode
            # thinking_mode=True,  # Если доступно
        )
        self.system_message = system_message

    async def async_get_response(self, messages: list):
        try:
            logger.info(
                f"Отправляем запрос в Gemini API с {len(messages)} сообщениями")
            logger.debug(
                f"Системное сообщение: {self.system_message[:100]}...")

            prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        self.system_message,
                    ),
                    MessagesPlaceholder(variable_name="messages"),
                ]
            )

            chain = prompt | self.client

            completion = await chain.ainvoke(
                {"messages": messages, }
            )

            # Детальное логирование ответа
            logger.info(f"Получен ответ от Gemini API")
            logger.debug(f"Тип ответа: {type(completion)}")
            logger.debug(f"Ответ целиком: {completion}")

            if hasattr(completion, 'content'):
                logger.debug(f"Содержимое ответа: '{completion.content}'")
                logger.debug(
                    f"Длина содержимого: {len(completion.content) if completion.content else 0}")
            else:
                logger.warning("У ответа нет атрибута 'content'")
                logger.debug(f"Доступные атрибуты: {dir(completion)}")

            # Улучшенная проверка на пустоту
            if not completion:
                raise ValueError("ИИ вернул None")

            if not hasattr(completion, 'content'):
                raise ValueError("У ответа ИИ нет атрибута 'content'")

            if completion.content is None:
                raise ValueError("ИИ вернул content = None")

            if completion.content.strip() == "":
                raise ValueError("ИИ вернул пустую строку")

            logger.info(
                f"Ответ ИИ успешно получен, длина: {len(completion.content)}")
            return completion

        except Exception as e:
            logger.error(f"Ошибка при запросе к Gemini API: {e}")
            logger.exception("Полная трассировка ошибки:")
            raise

    async def async_get_response_with_thinking(self, messages: list) -> AsyncGenerator[str, None]:
        """
        Генерирует ответ с симуляцией thinking progress
        """
        try:
            logger.info(f"Запуск thinking mode для {len(messages)} сообщений")

            # Фазы мышления на чеченском
            thinking_phases = [
                "Ойла йеш ву...",  # Думаю...
                "Анализ йу йоьдуш...",  # Анализирую...
                "Жоп вовшах тухуш ву...",  # Формулирую ответ...
                "Кечам бина волуш лаьтта...",  # Почти готово...
            ]

            # Показываем фазы мышления
            for i, phase in enumerate(thinking_phases):
                yield f"🧠 {phase}"
                # Ждем случайное время от 0.5 до 2 секунд
                await asyncio.sleep(0.5 + (i * 0.3))

            # Получаем реальный ответ
            prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        self.system_message,
                    ),
                    MessagesPlaceholder(variable_name="messages"),
                ]
            )

            chain = prompt | self.client
            completion = await chain.ainvoke({"messages": messages})

            if not completion or not hasattr(completion, 'content') or not completion.content or completion.content.strip() == "":
                yield "❌ ИИ цхьа а жоп ца делла"
                return

            # Возвращаем финальный ответ
            yield completion.content

        except Exception as e:
            logger.error(f"Ошибка в thinking mode: {e}")
            yield f"❌ Ошибка: {str(e)}"
