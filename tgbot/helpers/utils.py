from datetime import datetime
import os


def create_absolute_path(file_path: str, file_name: str, file_format: str, add_time: bool = False):
    full_file_path = f"{file_path}{file_name}"
    if add_time:
        current_datetime = datetime.now()
        formatted_datetime = current_datetime.strftime("%Y-%m-%d_%H-%M-%S")
        full_file_path += f"-{formatted_datetime}"
    full_file_path += f".{file_format}"
    absolute_file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), full_file_path))

    return absolute_file_path


def get_openai_system_message() -> str:
    system_message = """
Ты обычный человек.
Пользователь хочет просто поговорить.
Просто говори с ним, как человек.
На любую тему.
Можешь просить пользователя предложить тему.
Потом говори на эту тему, пока пользователь не сменит тему.
Просто веди диалог, как обычный человек, а не как ассистент.
"""
    return system_message