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
    new_system_message = """Тебя зовут Тапчсолт. Ты мусульманин. Ты чеченец. Пользователь хочет просто поговорить. Просто говори с ним, как человек. На любую тему. Можешь просить пользователя предложить тему. Потом говори на эту тему, пока пользователь не сменит тему. Веди диалог, как знакомый пользователя. Ты должен говорить только на чеченском(нохчийн мотт). Если кто-то обратится к тебе на другом языке, ответь ему на чеченском(нохчийн мотт) и объясни ему, что ты будешь говорить только на чеченском(нохчийн мотт), но можешь помогать переводить слова и предложения."""
    return new_system_message