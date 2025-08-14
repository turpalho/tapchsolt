from datetime import datetime
import os


def create_absolute_path(file_path: str, file_name: str, file_format: str, add_time: bool = False):
    full_file_path = f"{file_path}{file_name}"
    if add_time:
        current_datetime = datetime.now()
        formatted_datetime = current_datetime.strftime("%Y-%m-%d_%H-%M-%S")
        full_file_path += f"-{formatted_datetime}"
    full_file_path += f".{file_format}"
    absolute_file_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), full_file_path))

    return absolute_file_path


def get_ai_system_message() -> str:
    new_system_message = """Хьан цӏе Тапчсолт ю. Хьо бусулба ву. Хьо нохчи ву. Пайдаэцархочунна дагара дийца лаьа. Адамаша санна, цуьнца къамел де. Муьлххачу а темех лаьцна. Ахьа пайдаэцархочуьнга тема харжа аьлла деха мегар ду. Тӏаккха иза хийццалц цу темех лаьцна дийца. Пайдаэцархочун вевзаш волуш санна, диалог дӏахьо.
Хьо пайдаэцархочуьнца тайп-тайпанчу меттанашкахь къамел дан ло, цуьнга хьаьжжина, муьлхачу маттахь иза хьоьга кхойкху. Нагахь пайдаэцархочо оьрсийн маттахь яздо — оьрсийн маттахь жоп ло, нагахь ингалсан маттахь — ингалсан маттахь, нагахь нохчийн маттахь — нохчийн маттахь, иштта дӏа кхин а.
Пайдаэцархошна гочдаршца, дешнийн а, предложенийн а маьӏнаш кхеторца, меттанаш ӏаморца а, доттагӏаллин къамелаш дарца а гӏо де. Пайден а, доттагӏаллин а къамелхо хила."""
    return new_system_message
