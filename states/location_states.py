from aiogram.fsm.state import StatesGroup, State


class AddLocation(StatesGroup):
    name = State()
    description = State()
    region = State()
    new_region = State()
    street = State()
    new_street = State()
    coordinates = State()
    phone_numbers = State()
    images = State()
    mark_main_image = State()  # pick which uploaded image is "main"
    tag_group = State()
    new_tag_group = State()
    tags = State()
    confirm = State()
