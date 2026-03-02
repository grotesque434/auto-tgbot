from aiogram.fsm.state import State, StatesGroup


class ContentCreation(StatesGroup):
    waiting_for_prompt = State()
    choosing_topic = State()
    reviewing_script = State()
    reviewing_storyboard = State()
    choosing_media_type = State()
    generating = State()


class Publishing(StatesGroup):
    choosing_record = State()
    confirming_publish = State()
    setting_privacy = State()
