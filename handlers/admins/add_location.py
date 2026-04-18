from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    Message, CallbackQuery,
    InlineQuery, InlineQueryResultArticle, InputTextMessageContent,
)

from keyboards.admin_kb import (
    admin_main_kb, session_cancel_kb, cancel_kb,
    regions_kb, streets_kb,
    phones_kb, images_kb, images_done_kb,
    mark_main_image_kb, tag_groups_kb, tags_kb, confirm_kb,
)
from modles.locations import (
    Region, Street, Location, PhoneNumbers, Images,
    Tag, TagGroup, LocationTags, User,
)
from states.location_states import AddLocation

router = Router()


# ──────────────────────────────────────────────
# CANCEL  (works from any AddLocation state)
# ──────────────────────────────────────────────

@router.message(StateFilter(AddLocation), F.text == "❌ Bekor qilish")
async def cancel_via_reply(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Bekor qilindi.", reply_markup=admin_main_kb())


@router.callback_query(F.data == "add:cancel")
async def cancel_via_inline(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer("❌ Bekor qilindi.", reply_markup=admin_main_kb())
    await callback.answer()


# ──────────────────────────────────────────────
# 1. Start
# ──────────────────────────────────────────────

@router.message(F.text == "📍 Info qo'shish")
async def start_add_location(message: Message, state: FSMContext):
    await state.set_state(AddLocation.name)
    await message.answer(
        "📝 Joylashuv nomini kiriting:",
        reply_markup=session_cancel_kb(),
    )


# ──────────────────────────────────────────────
# 2. Name → Description
# ──────────────────────────────────────────────

@router.message(AddLocation.name)
async def get_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(AddLocation.description)
    await message.answer("📄 Qisqacha tavsif kiriting:", reply_markup=cancel_kb())


# ──────────────────────────────────────────────
# 3. Description → Region
# ──────────────────────────────────────────────

@router.message(AddLocation.description)
async def get_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await state.set_state(AddLocation.region)
    regions = await Region.all()
    await message.answer(
        "🌍 Regionni tanlang yoki yangisini qo'shing:",
        reply_markup=regions_kb(regions),
    )


# ──────────────────────────────────────────────
# 4. Region
# ──────────────────────────────────────────────

@router.callback_query(AddLocation.region, F.data.startswith("region:"))
async def select_region(callback: CallbackQuery, state: FSMContext):
    value = callback.data.split(":", 1)[1]
    await callback.answer()

    if value == "new":
        await state.set_state(AddLocation.new_region)
        await callback.message.answer("✏️ Yangi region nomini kiriting:", reply_markup=cancel_kb())
        return

    region = await Region.get(id=int(value))
    await state.update_data(region_id=region.id, region_name=region.name)
    await callback.message.answer(f"✅ Region: <b>{region.name}</b>", parse_mode="HTML")
    await _show_streets(callback.message, state, region.id)


@router.message(AddLocation.new_region)
async def create_region(message: Message, state: FSMContext):
    region = await Region.create(name=message.text.strip())
    await state.update_data(region_id=region.id, region_name=region.name)
    await message.answer(f"✅ Yangi region yaratildi: <b>{region.name}</b>", parse_mode="HTML")
    await _show_streets(message, state, region.id)


async def _show_streets(message: Message, state: FSMContext, region_id: int):
    await state.set_state(AddLocation.street)
    streets = await Street.filter(region_id=region_id)
    await message.answer(
        "🛣 Ko'chani tanlang yoki yangisini qo'shing:",
        reply_markup=streets_kb(streets),
    )


# ──────────────────────────────────────────────
# 5. Street
# ──────────────────────────────────────────────

@router.callback_query(AddLocation.street, F.data.startswith("street:"))
async def select_street(callback: CallbackQuery, state: FSMContext):
    value = callback.data.split(":", 1)[1]
    await callback.answer()

    if value == "new":
        await state.set_state(AddLocation.new_street)
        await callback.message.answer("✏️ Yangi ko'cha nomini kiriting:", reply_markup=cancel_kb())
        return

    street = await Street.get(id=int(value))
    await state.update_data(street_id=street.id, street_name=street.name)
    await callback.message.answer(f"✅ Ko'cha: <b>{street.name}</b>", parse_mode="HTML")
    await _ask_coords(callback.message, state)


@router.message(AddLocation.new_street)
async def create_street(message: Message, state: FSMContext):
    data = await state.get_data()
    street = await Street.create(name=message.text.strip(), region_id=data["region_id"])
    await state.update_data(street_id=street.id, street_name=street.name)
    await message.answer(f"✅ Yangi ko'cha yaratildi: <b>{street.name}</b>", parse_mode="HTML")
    await _ask_coords(message, state)


# ──────────────────────────────────────────────
# 6. Coordinates
# ──────────────────────────────────────────────

async def _ask_coords(message: Message, state: FSMContext):
    await state.set_state(AddLocation.coordinates)
    await message.answer(
        "📍 Koordinatalarni kiriting:\n"
        "• Lokatsiya yuboring\n"
        "• Yoki matn: <code>41.2995, 69.2401</code>",
        parse_mode="HTML",
        reply_markup=cancel_kb(),
    )


@router.message(AddLocation.coordinates, F.location)
async def get_coords_location(message: Message, state: FSMContext):
    lat, lon = message.location.latitude, message.location.longitude
    await state.update_data(lat=lat, lon=lon)
    await message.answer(f"✅ Koordinatalar: <code>{lat}, {lon}</code>", parse_mode="HTML")
    await _ask_phones(message, state)


@router.message(AddLocation.coordinates)
async def get_coords_text(message: Message, state: FSMContext):
    try:
        parts = message.text.replace(" ", "").split(",")
        lat, lon = float(parts[0]), float(parts[1])
    except (ValueError, IndexError):
        await message.answer(
            "❌ Noto'g'ri format. Qaytadan kiriting: <code>lat, lon</code>",
            parse_mode="HTML",
        )
        return
    await state.update_data(lat=lat, lon=lon)
    await message.answer(f"✅ Koordinatalar: <code>{lat}, {lon}</code>", parse_mode="HTML")
    await _ask_phones(message, state)


# ──────────────────────────────────────────────
# 7. Phone numbers
# ──────────────────────────────────────────────

async def _ask_phones(message: Message, state: FSMContext):
    await state.set_state(AddLocation.phone_numbers)
    await state.update_data(phones=[])
    await message.answer(
        "📞 Telefon raqam(lar)ini kiriting.\n"
        "Har birini alohida xabar qiling, tugagach ✅ tugmasini bosing:",
        reply_markup=phones_kb(),
    )


@router.message(AddLocation.phone_numbers)
async def get_phone(message: Message, state: FSMContext):
    data = await state.get_data()
    phones: list = data.get("phones", [])
    phones.append(message.text.strip())
    await state.update_data(phones=phones)
    await message.answer(
        f"➕ Qo'shildi: <code>{message.text.strip()}</code>\n"
        f"Jami: <b>{len(phones)}</b> ta raqam\n"
        "Yana qo'shing yoki tugating:",
        reply_markup=phones_kb(),
        parse_mode="HTML",
    )


@router.callback_query(AddLocation.phone_numbers, F.data == "phones:done")
async def phones_done(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await _ask_images(callback.message, state)


# ──────────────────────────────────────────────
# 8. Images
# ──────────────────────────────────────────────

async def _ask_images(message: Message, state: FSMContext):
    await state.set_state(AddLocation.images)
    await state.update_data(images=[])
    await message.answer(
        "🖼 Rasmlar yuboring.\n"
        "Rasm yo'q bo'lsa ⏭ tugmasini bosing:",
        reply_markup=images_kb(),
    )


@router.message(AddLocation.images, F.photo)
async def get_image(message: Message, state: FSMContext):
    data = await state.get_data()
    images: list = data.get("images", [])
    images.append(message.photo[-1].file_id)
    await state.update_data(images=images)
    await message.answer(
        f"✅ Rasm qo'shildi ({len(images)} ta). Yana yuboring yoki tugating:",
        reply_markup=images_done_kb(),
    )


@router.callback_query(AddLocation.images, F.data.in_({"images:done", "images:skip"}))
async def images_done(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    data = await state.get_data()
    images: list = data.get("images", [])

    if len(images) > 1:
        await _ask_mark_main(callback.message, state, images, current=0)
    else:
        await _ask_tag_group(callback.message, state)


# ──────────────────────────────────────────────
# 8b. Mark main image
# ──────────────────────────────────────────────

async def _ask_mark_main(message: Message, state: FSMContext, images: list, current: int):
    await state.set_state(AddLocation.mark_main_image)
    await state.update_data(main_image_idx=current)
    # Send each uploaded photo so admin can see which number is which
    for i, file_id in enumerate(images):
        label = f"✅ Asosiy — rasm #{i + 1}" if i == current else f"Rasm #{i + 1}"
        await message.answer_photo(photo=file_id, caption=label)
    await message.answer(
        "📌 Qaysi rasm asosiy bo'lsin? Tanlang:",
        reply_markup=mark_main_image_kb(len(images), current),
    )


@router.callback_query(AddLocation.mark_main_image, F.data.startswith("main_img:"))
async def mark_main_image_cb(callback: CallbackQuery, state: FSMContext):
    value = callback.data.split(":")[1]

    if value == "confirm":
        await callback.answer()
        await _ask_tag_group(callback.message, state)
        return

    idx = int(value)
    data = await state.get_data()
    images: list = data.get("images", [])
    await state.update_data(main_image_idx=idx)

    await callback.message.edit_reply_markup(
        reply_markup=mark_main_image_kb(len(images), idx)
    )
    await callback.answer(f"✅ Rasm #{idx + 1} asosiy sifatida belgilandi")


# ──────────────────────────────────────────────
# 9. Tag groups
# ──────────────────────────────────────────────

async def _ask_tag_group(message: Message, state: FSMContext):
    await state.set_state(AddLocation.tag_group)
    if "selected_tags" not in (await state.get_data()):
        await state.update_data(selected_tags=[])
    groups = await TagGroup.all()
    await message.answer(
        "🏷 Teg guruhini tanlang yoki yangi guruh yarating:",
        reply_markup=tag_groups_kb(groups),
    )


@router.callback_query(AddLocation.tag_group, F.data == "tags:skip")
async def skip_tags(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await _show_confirm(callback.message, state)


@router.callback_query(AddLocation.tag_group, F.data == "taggroup:new")
async def new_tag_group_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AddLocation.new_tag_group)
    await callback.message.answer(
        "✏️ Yangi teg guruhi nomini kiriting:", reply_markup=cancel_kb()
    )
    await callback.answer()


@router.message(AddLocation.new_tag_group)
async def new_tag_group_save(message: Message, state: FSMContext):
    group = await TagGroup.create(name=message.text.strip())
    await message.answer(
        f"✅ Yangi guruh yaratildi: <b>{group.name}</b>\n"
        "Endi shu guruhdan teg tanlang:",
        parse_mode="HTML",
    )
    # Go straight into this group's tag selection
    await state.update_data(current_group_id=group.id, current_group_name=group.name)
    await state.set_state(AddLocation.tags)
    data = await state.get_data()
    selected = data.get("selected_tags", [])
    await message.answer(
        f"🏷 <b>{group.name}</b> — teglarni qidiring va tanlang:",
        reply_markup=tags_kb(selected, group.id),
        parse_mode="HTML",
    )


@router.callback_query(AddLocation.tag_group, F.data.startswith("taggroup:"))
async def select_tag_group(callback: CallbackQuery, state: FSMContext):
    group_id = int(callback.data.split(":")[1])
    group = await TagGroup.get(id=group_id)
    await state.update_data(current_group_id=group_id, current_group_name=group.name)
    await state.set_state(AddLocation.tags)

    data = await state.get_data()
    selected = data.get("selected_tags", [])
    selected_text = ", ".join(t["name"] for t in selected) if selected else "yo'q"

    await callback.message.answer(
        f"🏷 <b>{group.name}</b> guruhidan teglarni tanlang.\n"
        f"Tanlangan: {selected_text}\n\n"
        "🔍 tugmasi orqali teg qidiring va tanlang:",
        reply_markup=tags_kb(selected, group_id),
        parse_mode="HTML",
    )
    await callback.answer()


# ──────────────────────────────────────────────
# 10. Tags
# ──────────────────────────────────────────────

@router.callback_query(AddLocation.tags, F.data.startswith("tag:remove:"))
async def remove_tag(callback: CallbackQuery, state: FSMContext):
    tag_id = int(callback.data.split(":")[2])
    data = await state.get_data()
    selected: list = data.get("selected_tags", [])
    selected = [t for t in selected if t["id"] != tag_id]
    await state.update_data(selected_tags=selected)

    group_id = data.get("current_group_id")
    await callback.message.edit_reply_markup(reply_markup=tags_kb(selected, group_id))
    await callback.answer("❌ Teg olib tashlandi")


@router.callback_query(AddLocation.tags, F.data == "tags:back")
async def tags_back(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    # Re-show the group list (keeping already-selected tags)
    await state.set_state(AddLocation.tag_group)
    groups = await TagGroup.all()
    await callback.message.answer(
        "🏷 Boshqa teg guruhini tanlang:",
        reply_markup=tag_groups_kb(groups),
    )


@router.callback_query(F.data == "tags:done")
async def tags_done(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await _show_confirm(callback.message, state)


# ──────────────────────────────────────────────
# Inline query — tag search
# Format: "tag:{group_id}:{search}"
# ──────────────────────────────────────────────

@router.inline_query(F.query.startswith("tag:"))
async def inline_tag_search(inline_query: InlineQuery):
    parts = inline_query.query.split(":", 2)
    if len(parts) < 3:
        await inline_query.answer([], cache_time=1)
        return

    try:
        group_id = int(parts[1])
    except ValueError:
        await inline_query.answer([], cache_time=1)
        return

    search = parts[2].strip()

    if search:
        tags = await Tag.filter(tag_group_id=group_id, name__icontains=search).limit(20)
    else:
        tags = await Tag.filter(tag_group_id=group_id).limit(20)

    results = []
    exact_match = False

    for tag in tags:
        if tag.name.lower() == search.lower():
            exact_match = True
        results.append(
            InlineQueryResultArticle(
                id=f"tag_{tag.id}",
                title=tag.name,
                description="Tegni tanlash uchun bosing",
                input_message_content=InputTextMessageContent(
                    message_text=f"✅tag_selected:{tag.id}:{tag.name}"
                ),
            )
        )

    # Offer to create new tag if no exact match and search is not empty
    if search and not exact_match:
        results.append(
            InlineQueryResultArticle(
                id="new_tag",
                title=f"➕ Yaratish: {search}",
                description=f'"{search}" nomli yangi teg yaratish',
                input_message_content=InputTextMessageContent(
                    message_text=f"✅tag_create:{group_id}:{search}"
                ),
            )
        )

    await inline_query.answer(results, cache_time=1)


# Intercept tag selected message (sent from inline result)
@router.message(AddLocation.tags, F.text.startswith("✅tag_selected:"))
async def handle_tag_selected(message: Message, state: FSMContext):
    _, tag_id_str, tag_name = message.text.split(":", 2)
    tag_id = int(tag_id_str)

    data = await state.get_data()
    selected: list = data.get("selected_tags", [])

    if not any(t["id"] == tag_id for t in selected):
        selected.append({"id": tag_id, "name": tag_name})
        await state.update_data(selected_tags=selected)
        notice = f"✅ Teg qo'shildi: <b>{tag_name}</b>"
    else:
        notice = f"ℹ️ <b>{tag_name}</b> allaqachon tanlangan"

    group_id = data.get("current_group_id")
    selected_text = ", ".join(t["name"] for t in selected)

    await message.delete()
    await message.answer(
        f"{notice}\nTanlangan: {selected_text}",
        reply_markup=tags_kb(selected, group_id),
        parse_mode="HTML",
    )


# Intercept tag create message (sent from inline result)
@router.message(AddLocation.tags, F.text.startswith("✅tag_create:"))
async def handle_tag_create(message: Message, state: FSMContext):
    _, group_id_str, tag_name = message.text.split(":", 2)
    group_id = int(group_id_str)

    tag = await Tag.create(name=tag_name.strip(), tag_group_id=group_id)

    data = await state.get_data()
    selected: list = data.get("selected_tags", [])
    selected.append({"id": tag.id, "name": tag.name})
    await state.update_data(selected_tags=selected)

    selected_text = ", ".join(t["name"] for t in selected)

    await message.delete()
    await message.answer(
        f"✅ Yangi teg yaratildi va qo'shildi: <b>{tag.name}</b>\nTanlangan: {selected_text}",
        reply_markup=tags_kb(selected, group_id),
        parse_mode="HTML",
    )


# ──────────────────────────────────────────────
# 11. Confirm
# ──────────────────────────────────────────────

async def _show_confirm(message: Message, state: FSMContext):
    await state.set_state(AddLocation.confirm)
    data = await state.get_data()

    phones = data.get("phones", [])
    images = data.get("images", [])
    selected_tags = data.get("selected_tags", [])

    phones_text = "\n".join(f"  • {p}" for p in phones) if phones else "  yo'q"
    tags_text = ", ".join(t["name"] for t in selected_tags) if selected_tags else "yo'q"

    text = (
        "📋 <b>Ma'lumotlarni tasdiqlang:</b>\n\n"
        f"📍 <b>Nom:</b> {data.get('name')}\n"
        f"📄 <b>Tavsif:</b> {data.get('description')}\n"
        f"🌍 <b>Region:</b> {data.get('region_name')}\n"
        f"🛣 <b>Ko'cha:</b> {data.get('street_name')}\n"
        f"📡 <b>Koordinatalar:</b> {data.get('lat')}, {data.get('lon')}\n"
        f"📞 <b>Telefonlar:</b>\n{phones_text}\n"
        f"🖼 <b>Rasmlar:</b> {len(images)} ta\n"
        f"🏷 <b>Teglar:</b> {tags_text}"
    )
    await message.answer(text, reply_markup=confirm_kb(), parse_mode="HTML")


@router.callback_query(AddLocation.confirm, F.data == "confirm:yes")
async def save_location(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    user, _ = await User.get_or_create(
        tg_id=callback.from_user.id,
        defaults={
            "username": callback.from_user.username or "",
            "first_name": callback.from_user.first_name or "",
            "last_name": callback.from_user.last_name or "",
            "phone_number": "",
            "role": "admin",
        },
    )

    location = await Location.create(
        name=data["name"],
        description=data["description"],
        street_id=data["street_id"],
        lat=data["lat"],
        lon=data["lon"],
        created_by_id=user.id,
        owner_id=user.id,
    )

    for phone in data.get("phones", []):
        await PhoneNumbers.create(location=location, phone_number=phone)

    main_idx = data.get("main_image_idx", 0)
    for i, file_id in enumerate(data.get("images", [])):
        await Images.create(
            location=location,
            image_local_path="",
            image_tg_file_id=file_id,
            is_main=(i == main_idx),
        )

    for tag_data in data.get("selected_tags", []):
        await LocationTags.create(location=location, tag_id=tag_data["id"])

    await state.clear()
    await callback.message.answer(
        f"✅ <b>{data['name']}</b> muvaffaqiyatli saqlandi!",
        reply_markup=admin_main_kb(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(AddLocation.confirm, F.data == "confirm:no")
async def cancel_location(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer("❌ Bekor qilindi.", reply_markup=admin_main_kb())
    await callback.answer()
