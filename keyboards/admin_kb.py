from aiogram.types import (
    ReplyKeyboardMarkup,
    InlineKeyboardMarkup, InlineKeyboardButton,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

# ── Shared cancel row ─────────────────────────────────────────────────────────
_CANCEL = InlineKeyboardButton(text="❌ Bekor qilish", callback_data="add:cancel")


def _add_cancel(builder: InlineKeyboardBuilder) -> None:
    """Append a cancel row to any InlineKeyboardBuilder in-place."""
    builder.row(_CANCEL)


# ── Main menu ─────────────────────────────────────────────────────────────────

def admin_main_kb() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text="📍 Info qo'shish")
    builder.button(text="🔍 Qidiruv")
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)


def session_cancel_kb() -> ReplyKeyboardMarkup:
    """Persistent reply-keyboard shown during the whole add-location session."""
    builder = ReplyKeyboardBuilder()
    builder.button(text="❌ Bekor qilish")
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=False)


# ── Add-location flow keyboards ───────────────────────────────────────────────

def cancel_kb() -> InlineKeyboardMarkup:
    """Standalone inline cancel — used on text-input-only steps."""
    builder = InlineKeyboardBuilder()
    builder.row(_CANCEL)
    return builder.as_markup()


def regions_kb(regions) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for region in regions:
        builder.button(text=region.name, callback_data=f"region:{region.id}")
    builder.button(text="➕ Yangi region", callback_data="region:new")
    builder.adjust(2)
    _add_cancel(builder)
    return builder.as_markup()


def streets_kb(streets) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for street in streets:
        builder.button(text=street.name, callback_data=f"street:{street.id}")
    builder.button(text="➕ Yangi ko'cha", callback_data="street:new")
    builder.adjust(2)
    _add_cancel(builder)
    return builder.as_markup()


def phones_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Tugatish", callback_data="phones:done")
    _add_cancel(builder)
    return builder.as_markup()


def images_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="⏭ O'tkazib yuborish", callback_data="images:skip")
    builder.button(text="✅ Tugatish", callback_data="images:done")
    builder.adjust(2)
    _add_cancel(builder)
    return builder.as_markup()


def images_done_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Tugatish", callback_data="images:done")
    _add_cancel(builder)
    return builder.as_markup()


def tag_groups_kb(groups) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for group in groups:
        builder.button(text=group.name, callback_data=f"taggroup:{group.id}")
    builder.adjust(2)
    builder.row(
        InlineKeyboardButton(text="➕ Yangi guruh", callback_data="taggroup:new"),
        InlineKeyboardButton(text="⏩ O'tkazib yuborish", callback_data="tags:skip"),
    )
    _add_cancel(builder)
    return builder.as_markup()


def tags_kb(selected_tags: list, group_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for tag in selected_tags:
        builder.button(
            text=f"❌ {tag['name']}",
            callback_data=f"tag:remove:{tag['id']}",
        )
    if selected_tags:
        builder.adjust(2)
    builder.row(
        InlineKeyboardButton(
            text="🔍 Teg qidirish / qo'shish",
            switch_inline_query_current_chat=f"tag:{group_id}:",
        )
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Boshqa guruh", callback_data="tags:back"),
        InlineKeyboardButton(text="✅ Saqlash", callback_data="tags:done"),
    )
    _add_cancel(builder)
    return builder.as_markup()


def mark_main_image_kb(count: int, current: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for i in range(count):
        label = f"✅ {i + 1}" if i == current else str(i + 1)
        builder.button(text=label, callback_data=f"main_img:{i}")
    builder.adjust(5)
    builder.row(InlineKeyboardButton(text="✔️ Tasdiqlash", callback_data="main_img:confirm"))
    _add_cancel(builder)
    return builder.as_markup()


def confirm_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Tasdiqlash", callback_data="confirm:yes")
    builder.button(text="❌ Bekor qilish", callback_data="add:cancel")
    builder.adjust(2)
    return builder.as_markup()
