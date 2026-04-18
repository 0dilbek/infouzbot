"""
Inline query location search.

Result format:
  • Barcha natijalar → InlineQueryResultArticle  (ro'yxat ko'rinishi)
    Rasm bor bo'lsa xabarga yashirin link qo'shiladi — Telegram uni
    link preview sifatida yuqorida ko'rsatadi (rasm + matn birgalikda).

Tanlanganda:
  • [rasm preview] + qisqa matn + [📋 Batafsil] tugmasi

"📋 Batafsil" bosilganda:
  1. Xabar to'liq matn bilan tahrirlanadi (preview o'chadi), keyboard olib tashlanadi
  2. Rasmlar media group sifatida alohida yuboriladi
     (inline → DM, oddiy chat → o'sha chatga)

Qidiruv: barcha so'z kombinatsiyalari, uzunroq ibora = yuqori ball.
Sahifalash: Telegram next_offset, 10 tadan.
"""

import logging
from itertools import combinations as iter_combinations

from aiogram import Bot, F, Router
from aiogram.client.telegram import PRODUCTION
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQuery,
    InlineQueryResultArticle,
    InputMediaPhoto,
    InputTextMessageContent,
    Message,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from tortoise.expressions import Q

from modles.locations import Location

router = Router()

PAGE = 10


# ═══════════════════════════════════════════════════════════
#  QIDIRUV MEXANIZMI
# ═══════════════════════════════════════════════════════════

def _build_phrases(query: str) -> list[tuple[str, int]]:
    words = query.strip().split()
    if not words:
        return []
    seen: set[str] = set()
    result: list[tuple[str, int]] = []
    for length in range(len(words), 0, -1):
        for combo in iter_combinations(range(len(words)), length):
            phrase = " ".join(words[i] for i in combo)
            key = phrase.casefold()
            if key not in seen:
                seen.add(key)
                result.append((phrase, length * length))
    return result


async def _search_ids(query: str) -> list[int]:
    scored: dict[int, int] = {}
    for phrase, weight in _build_phrases(query):
        q = (
            Q(name__icontains=phrase)
            | Q(description__icontains=phrase)
            | Q(tags__tag__name__icontains=phrase)
            | Q(street__name__icontains=phrase)
            | Q(street__region__name__icontains=phrase)
        )
        ids = await Location.filter(q).distinct().values_list("id", flat=True)
        for lid in ids:
            scored[lid] = scored.get(lid, 0) + weight
    return sorted(scored, key=lambda x: -scored[x])


# ═══════════════════════════════════════════════════════════
#  MA'LUMOT YORDAMCHILARI
# ═══════════════════════════════════════════════════════════

async def _load(loc_id: int) -> Location:
    return await Location.get(id=loc_id).prefetch_related(
        "street", "street__region",
        "tags__tag",
        "phone_numbers",
        "images",
    )


def _place(loc: Location) -> str:
    try:
        return f"{loc.street.region.name} › {loc.street.name}"
    except AttributeError:
        return "—"


async def _tag_names(loc: Location) -> list[str]:
    lts = await loc.tags.all().prefetch_related("tag")
    return [lt.tag.name for lt in lts]


async def _phones(loc: Location) -> list[str]:
    return [p.phone_number for p in await loc.phone_numbers.all()]


async def _sorted_images(loc: Location) -> list:
    imgs = await loc.images.all()
    return sorted(imgs, key=lambda img: (not img.is_main,))


async def _file_url(file_id: str, bot: Bot) -> str | None:
    try:
        file = await bot.get_file(file_id)
        url = PRODUCTION.file_url(bot.token, file.file_path)
        logging.info("_file_url: %s", url)
        return url
    except Exception as e:
        logging.error("_file_url error: %s", e)
        return None


# ═══════════════════════════════════════════════════════════
#  MATN FORMATLASH
# ═══════════════════════════════════════════════════════════

async def _brief(loc: Location) -> str:
    phones = await _phones(loc)
    lines = [f"📍 <b>{loc.name}</b>", f"🌍 {_place(loc)}"]
    if phones:
        lines.append(f"📞 {phones[0]}")
    return "\n".join(lines)


async def _full(loc: Location) -> str:
    tags = await _tag_names(loc)
    phones = await _phones(loc)
    phones_block = "\n".join(f"  • {p}" for p in phones) if phones else "  yo'q"
    tags_str = " · ".join(tags) if tags else "yo'q"
    maps = f"https://maps.google.com/?q={loc.lat},{loc.lon}"
    return "\n".join([
        f"📍 <b>{loc.name}</b>",
        "",
        f"📝 {loc.description}",
        "",
        f"🌍 <b>{_place(loc)}</b>",
        f'🗺 <a href="{maps}">Xaritada ko\'rish</a>',
        "",
        f"📞 <b>Telefon:</b>\n{phones_block}",
        "",
        f"🏷 {tags_str}",
    ])


# ═══════════════════════════════════════════════════════════
#  KLAVIATURALAR
# ═══════════════════════════════════════════════════════════

def _brief_kb(loc_id: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="📋 Batafsil", callback_data=f"loc_d:{loc_id}")
    return b.as_markup()


# ═══════════════════════════════════════════════════════════
#  INLINE QUERY HANDLERI
# ═══════════════════════════════════════════════════════════

@router.inline_query(~F.query.startswith("tag:"))
async def handle_inline_query(inline_query: InlineQuery, bot: Bot):
    query = inline_query.query.strip()
    try:
        offset = int(inline_query.offset) if inline_query.offset else 0
    except ValueError:
        offset = 0

    if query:
        all_ids = await _search_ids(query)
    else:
        all_ids = list(
            await Location.all().order_by("-id").values_list("id", flat=True)
        )

    page_ids = all_ids[offset: offset + PAGE]
    next_offset = str(offset + PAGE) if offset + PAGE < len(all_ids) else ""

    results = []
    for loc_id in page_ids:
        try:
            loc = await _load(loc_id)
        except Exception:
            continue

        tags = await _tag_names(loc)
        place = _place(loc)
        description = f"📍 {place}" + (f"  ·  🏷 {', '.join(tags[:3])}" if tags else "")
        brief_text = await _brief(loc)
        kb = _brief_kb(loc.id)
        images = await _sorted_images(loc)

        if images:
            url = await _file_url(images[0].image_tg_file_id, bot)
            # Yashirin link — Telegram link preview sifatida rasmni ko'rsatadi
            msg_text = f'<a href="{url}">\u200b</a>{brief_text}' if url else brief_text
        else:
            url = None
            msg_text = brief_text

        results.append(
            InlineQueryResultArticle(
                id=str(loc_id),
                title=loc.name,
                description=description,
                thumbnail_url=url,
                input_message_content=InputTextMessageContent(
                    message_text=msg_text,
                    parse_mode="HTML",
                    disable_web_page_preview=not bool(url),
                ),
                reply_markup=kb,
            )
        )

    await inline_query.answer(
        results,
        next_offset=next_offset,
        cache_time=30,
        is_personal=True,
    )


# ═══════════════════════════════════════════════════════════
#  BATAFSIL CALLBACK
# ═══════════════════════════════════════════════════════════

@router.callback_query(F.data.startswith("loc_d:"))
async def expand_detail(callback: CallbackQuery, bot: Bot):
    loc_id = int(callback.data.split(":")[1])
    try:
        loc = await _load(loc_id)
    except Exception:
        await callback.answer("Joylashuv topilmadi.", show_alert=True)
        return

    images = await _sorted_images(loc)
    full_text = await _full(loc)

    if callback.inline_message_id:
        await bot.edit_message_text(
            inline_message_id=callback.inline_message_id,
            text=full_text,
            parse_mode="HTML",
            disable_web_page_preview=True,
            reply_markup=None,
        )
        target_chat = callback.from_user.id
    else:
        await callback.message.edit_text(
            text=full_text,
            parse_mode="HTML",
            disable_web_page_preview=True,
            reply_markup=None,
        )
        target_chat = callback.message.chat.id

    if len(images) > 1:
        await bot.send_media_group(
            chat_id=target_chat,
            media=[InputMediaPhoto(media=img.image_tg_file_id) for img in images],
        )
    elif len(images) == 1:
        await bot.send_photo(
            chat_id=target_chat,
            photo=images[0].image_tg_file_id,
        )

    await callback.answer()


# ═══════════════════════════════════════════════════════════
#  QIDIRUV TUGMASI  (reply keyboard → inline rejim)
# ═══════════════════════════════════════════════════════════

@router.message(F.text == "🔍 Qidiruv")
async def search_hint(message: Message):
    b = InlineKeyboardBuilder()
    b.row(
        InlineKeyboardButton(
            text="🔍 Qidirish",
            switch_inline_query_current_chat="",
        )
    )
    await message.answer(
        "Joylashuvlarni qidirish uchun quyidagi tugmani bosing:\n"
        "<i>Nom, teg yoki manzil bo'yicha qidirish mumkin.</i>",
        reply_markup=b.as_markup(),
        parse_mode="HTML",
    )
