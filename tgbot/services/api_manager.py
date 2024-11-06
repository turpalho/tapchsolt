from typing import Any
import requests

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessage
from langchain_google_genai import ChatGoogleGenerativeAI


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
                {"messages": messages,}
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
                                                    model="gemini-1.5-pro",
                                                    temperature=1,
                                                    max_tokens=8000,
                                                    timeout=None,
                                                    max_retries=2,
                                                )
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

        completion = chain.invoke(
                {"messages": messages,}
            )
        return completion
