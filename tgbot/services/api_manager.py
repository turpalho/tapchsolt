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
    def __init__(self, api_key: str, system_message: str, proxy_url: str = None):
        import os

        # Если указан прокси, настраиваем переменные окружения
        if proxy_url:
            logger.info(f"Настраиваем Gemini API с прокси: {proxy_url}")

            # Проверяем тип прокси
            if proxy_url.startswith('https://'):
                logger.warning(
                    "⚠️ Прокси URL использует https://, рекомендуется http://")
                logger.warning("Пример: PROXY_URL=http://23.237.210.82:80")
            elif proxy_url.startswith('socks5://'):
                logger.info("🧅 Обнаружен SOCKS5 прокси (например, Tor)")
            elif proxy_url.startswith('socks4://'):
                logger.info("🔌 Обнаружен SOCKS4 прокси")

            # Устанавливаем переменные окружения для прокси
            # Это позволит всем HTTP-клиентам (включая те, что использует LangChain) использовать прокси
            os.environ['HTTP_PROXY'] = proxy_url
            os.environ['HTTPS_PROXY'] = proxy_url
            # Некоторые клиенты ищут в нижнем регистре
            os.environ['http_proxy'] = proxy_url
            os.environ['https_proxy'] = proxy_url

            # Для SOCKS прокси также устанавливаем ALL_PROXY
            if proxy_url.startswith(('socks4://', 'socks5://')):
                os.environ['ALL_PROXY'] = proxy_url
                os.environ['all_proxy'] = proxy_url

            logger.info("✅ Переменные окружения для прокси установлены")
        else:
            logger.info("Gemini API без прокси")

        self.client: ChatGoogleGenerativeAI = ChatGoogleGenerativeAI(
            api_key=api_key,
            # model="gemini-2.5-pro",
            model="gemini-2.5-flash",
            temperature=1,
            max_tokens=4096,
            timeout=None,
            max_retries=2,
            # Пробуем включить thinking mode
            # thinking_mode=True,  # Если доступно
        )
        self.system_message = system_message

    async def test_proxy_connection(self) -> bool:
        """
        Тестирует подключение через прокси
        """
        import httpx
        import os

        proxy_url = os.environ.get(
            'HTTPS_PROXY') or os.environ.get('HTTP_PROXY')

        if not proxy_url:
            logger.info("🔍 Прокси не настроен, тестирование пропущено")
            return True

        try:
            logger.info(f"🔍 Тестируем прокси подключение через {proxy_url}")

            # Тестируем прокси с простым HTTP запросом
            async with httpx.AsyncClient(proxy=proxy_url, timeout=10.0) as client:
                response = await client.get("https://httpbin.org/ip")

                if response.status_code == 200:
                    ip_info = response.json()
                    logger.info(
                        f"✅ Прокси работает! Внешний IP: {ip_info.get('origin', 'неизвестен')}")
                    return True
                else:
                    logger.error(f"❌ Прокси вернул код {response.status_code}")
                    return False

        except Exception as e:
            logger.error(f"❌ Ошибка тестирования прокси: {e}")
            logger.error(f"❌ Тип ошибки: {type(e).__name__}")

            # Детальная диагностика
            if "ConnectTimeout" in str(e) or "timeout" in str(e).lower():
                logger.error("⏰ Таймаут подключения - прокси не отвечает")
            elif "ConnectError" in str(e) or "connection" in str(e).lower():
                logger.error("🔌 Ошибка подключения - прокси недоступен")
            elif "ProxyError" in str(e):
                logger.error("🚫 Прокси отклонил подключение")
            else:
                logger.error(f"❓ Неизвестная ошибка: {e}")

            logger.error("💡 Проверьте корректность PROXY_URL в .env файле")
            return False

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
            error_message = str(e)
            logger.error(f"Ошибка при запросе к Gemini API: {error_message}")
            logger.exception("Полная трассировка ошибки:")

            # Специальная обработка ошибки геоблокировки
            if "User location is not supported for the API use" in error_message:
                logger.error("🚫 Обнаружена геоблокировка Gemini API!")

                # Тестируем прокси при обнаружении геоблокировки
                proxy_working = await self.test_proxy_connection()

                if not proxy_working:
                    logger.error(
                        "💡 Решение: настройте рабочий прокси в .env файле")
                    logger.error(
                        "Пример: PROXY_URL=http://username:password@proxy-server:port")
                    raise Exception(
                        "Geoblocking detected and proxy not working. Fix PROXY_URL in .env file. Example: PROXY_URL=http://user:pass@proxy:port")
                else:
                    logger.error(
                        "🤔 Прокси работает, но геоблокировка все еще активна")
                    logger.error(
                        "💡 Попробуйте другой прокси из поддерживаемого региона")
                    raise Exception(
                        "Geoblocking detected despite working proxy. Try proxy from supported region.")

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
            error_message = str(e)
            logger.error(f"Ошибка в thinking mode: {error_message}")

            # Специальная обработка ошибки геоблокировки
            if "User location is not supported for the API use" in error_message:
                logger.error("🚫 Обнаружена геоблокировка Gemini API!")

                # Тестируем прокси при обнаружении геоблокировки
                try:
                    proxy_working = await self.test_proxy_connection()
                    if not proxy_working:
                        yield "❌ Геоблокировка! Прокси не работает. Исправьте PROXY_URL в .env файле"
                    else:
                        yield "❌ Геоблокировка! Прокси работает, но нужен прокси из поддерживаемого региона"
                except:
                    yield "❌ Геоблокировка! Добавьте PROXY_URL в .env файл. Пример: PROXY_URL=http://user:pass@proxy:port"

            elif "Geoblocking detected" in error_message:
                yield "❌ Геоблокировка! Проверьте настройки прокси"
            else:
                yield f"❌ Ошибка: {error_message}"
