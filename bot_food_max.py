import asyncio
import os
import sqlite3
from datetime import datetime, timedelta
from maxapi import Bot, Dispatcher, F
from maxapi.types import MessageCreated, BotStarted, MessageCallback, Command

from config import (
    BOT_TOKEN, BUILDING_1_CHAT_ID, BUILDING_2_CHAT_ID,
    ADMIN_GROUP_MARCHENKO, ADMIN_GROUP_TANKISTOV
)
from keyboards_food import (
    main_menu, admin_menu, building_menu, stage_menu, stage_menu_home,
    grade_menu, litera_menu, category_menu, confirm_menu,
    report_period_menu, shift_menu, edit_class_menu,
    edit_category_menu, edit_quantity_menu, month_menu_teacher, month_menu_admin,
    class_selection_menu, home_grade_menu, after_school_building_menu, STAGE_NAMES,
    backdated_date_menu
)
from storage_food import (
    add_meal, add_meal_backdated, get_user_meals_today, create_excel_report_for_building,
    has_user_today_request, has_user_request_on_date, get_requests_by_shift, format_requests_by_shift,
    get_user_request_by_class, update_user_request, delete_user_request,
    get_all_classes_with_requests, get_all_requests_by_class, format_all_requests_by_class,
    get_user_requests_by_month, format_user_requests_by_month,
    get_requests_for_last_days, get_request_by_date, update_user_request_on_date,
    can_edit_request
)

# ========== ИНИЦИАЛИЗАЦИЯ БОТА ==========
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
user_states = {}
user_data = {}

ADMIN_GROUPS = [ADMIN_GROUP_MARCHENKO, ADMIN_GROUP_TANKISTOV]

def get_admin_building(chat_id: int) -> str:
    if chat_id == ADMIN_GROUP_MARCHENKO:
        return "Марченко"
    elif chat_id == ADMIN_GROUP_TANKISTOV:
        return "Танкистов"
    return None

def is_admin_group(chat_id: int) -> bool:
    return chat_id in ADMIN_GROUPS

# ========== ОСНОВНЫЕ ОБРАБОТЧИКИ ==========
@dp.message_created(Command('get_id'))
async def get_chat_id(event: MessageCreated):
    await event.message.answer(f"🆔 Chat ID: `{event.message.recipient.chat_id}`")

@dp.bot_started()
async def on_start(event: BotStarted):
    if is_admin_group(event.chat_id):
        await bot.send_message(chat_id=event.chat_id, text="🍽️ Бот-Ланчбокс (Администратор)",
                               attachments=[admin_menu()])
    else:
        await bot.send_message(chat_id=event.chat_id, text="🍽️ Бот-Ланчбокс готов принять заявку",
                               attachments=[main_menu()])

@dp.message_created(Command('start'))
async def cmd_start(event: MessageCreated):
    if is_admin_group(event.message.recipient.chat_id):
        await event.message.answer("🍽️ Бот-Ланчбокс (Администратор)", attachments=[admin_menu()])
    else:
        await event.message.answer("🍽️ Бот-Ланчбокс готов принять заявку", attachments=[main_menu()])

# ========== НОВАЯ ЗАЯВКА (ОБЫЧНАЯ) ==========
@dp.message_callback(F.callback.payload == "new_food_request")
async def new_request(event: MessageCallback):
    user_id = event.callback.user.user_id
    user_states[user_id] = {"step": "building"}
    user_data[user_id] = {"categories": {}}
    await bot.send_message(chat_id=event.message.recipient.chat_id, text="🏫 Выберите здание:",
                           attachments=[building_menu()])
    await event.answer()

# ========== НОВАЯ ЗАЯВКА ЗАДНИМ ЧИСЛОМ (АДМИН) ==========
@dp.message_callback(F.callback.payload == "backdated_request")
async def backdated_request_start(event: MessageCallback):
    if not is_admin_group(event.message.recipient.chat_id):
        await event.answer(notification="❌ Доступно только в группе администраторов")
        return
    
    user_id = event.callback.user.user_id
    await bot.send_message(
        chat_id=event.message.recipient.chat_id,
        text="📅 **Выберите дату для подачи заявки:**\n\n(доступны последние 3 дня)",
        attachments=[backdated_date_menu()]
    )
    await event.answer()

@dp.message_callback(F.callback.payload.startswith("back_date_"))
async def back_date_selected(event: MessageCallback):
    if not is_admin_group(event.message.recipient.chat_id):
        await event.answer(notification="❌ Доступно только в группе администраторов")
        return
    
    user_id = event.callback.user.user_id
    date_str = event.callback.payload.replace("back_date_", "")
    
    if date_str == "today":
        selected_date = datetime.now().strftime("%Y-%m-%d")
        selected_date_display = datetime.now().strftime("%d.%m.%Y")
    else:
        selected_date = date_str
        selected_date_display = datetime.strptime(selected_date, "%Y-%m-%d").strftime("%d.%m.%Y")
    
    # Сохраняем выбранную дату
    user_data[user_id] = {"back_date": selected_date, "categories": {}}
    user_states[user_id] = {"step": "building_backdated"}
    
    await bot.send_message(
        chat_id=event.message.recipient.chat_id,
        text=f"✅ Выбрана дата: {selected_date_display}\n\n🏫 Выберите здание:",
        attachments=[building_menu()]
    )
    await event.answer()

@dp.message_callback(F.callback.payload == "back_to_building")
async def back_to_building(event: MessageCallback):
    user_id = event.callback.user.user_id
    step = user_states.get(user_id, {}).get("step", "")
    
    if step == "building_backdated":
        user_states[user_id] = {"step": "building_backdated"}
    else:
        user_states[user_id] = {"step": "building"}
    
    await bot.send_message(chat_id=event.message.recipient.chat_id, text="🏫 Выберите здание:",
                           attachments=[building_menu()])
    await event.answer()

# ========== ВЫБОР ЗДАНИЯ (С ПРОДЛЕНКОЙ) ==========
@dp.message_callback(F.callback.payload.startswith("building_"))
async def select_building(event: MessageCallback):
    user_id = event.callback.user.user_id
    building_type = event.callback.payload.replace("building_", "")
    is_backdated = user_states.get(user_id, {}).get("step") == "building_backdated"
    
    if building_type == "Надомное":
        await select_home_building(event, is_backdated)
        return
    elif building_type == "Продленка":
        await select_after_school_building(event, is_backdated)
        return
    
    # Обычные здания
    building = building_type
    if user_id not in user_data:
        user_data[user_id] = {"categories": {}}
    user_data[user_id]["building"] = building
    user_states[user_id] = {"step": "stage_backdated" if is_backdated else "stage"}
    await bot.send_message(chat_id=event.message.recipient.chat_id, text=f"✅ Здание: {building}\n\n📚 Выберите ступень:",
                           attachments=[stage_menu()])
    await event.answer()

# ========== ПРОДЛЕНКА ==========
async def select_after_school_building(event: MessageCallback, is_backdated: bool = False):
    user_id = event.callback.user.user_id
    if user_id not in user_data:
        user_data[user_id] = {"categories": {}}
    user_states[user_id] = {"step": "after_school_building_backdated" if is_backdated else "after_school_building"}
    
    await bot.send_message(
        chat_id=event.message.recipient.chat_id,
        text="⏰ **Продленка**\n\nВыберите здание:",
        attachments=[after_school_building_menu()]
    )
    await event.answer()

@dp.message_callback(F.callback.payload.startswith("after_school_"))
async def after_school_building_choice(event: MessageCallback):
    user_id = event.callback.user.user_id
    building = event.callback.payload.replace("after_school_", "")
    is_backdated = "backdated" in user_states.get(user_id, {}).get("step", "")
    
    user_data[user_id]["building"] = building
    user_data[user_id]["stage"] = "after_school"
    user_data[user_id]["stage_name"] = "Продленка"
    user_states[user_id] = {"step": "after_school_class_backdated" if is_backdated else "after_school_class"}
    
    await bot.send_message(
        chat_id=event.message.recipient.chat_id,
        text=f"✅ Здание: {building}\n\n📖 **Введите класс (например: 1.5, 1.2):**"
    )
    await event.answer()

# ========== НАДОМНОЕ ОТДЕЛЕНИЕ ==========
async def select_home_building(event: MessageCallback, is_backdated: bool = False):
    user_id = event.callback.user.user_id
    building = "Надомное"
    if user_id not in user_data:
        user_data[user_id] = {"categories": {}}
    user_data[user_id]["building"] = building
    user_data[user_id]["stage"] = "home"
    user_data[user_id]["stage_name"] = "Надомное отделение"
    user_states[user_id] = {"step": "home_stage_backdated" if is_backdated else "home_stage"}
    
    await bot.send_message(
        chat_id=event.message.recipient.chat_id,
        text=f"✅ Здание: {building}\n\n🏠 **Выберите ступень:**",
        attachments=[stage_menu_home()]
    )
    await event.answer()

@dp.message_callback(F.callback.payload.startswith("home_stage_"))
async def select_home_stage(event: MessageCallback):
    user_id = event.callback.user.user_id
    stage = event.callback.payload.replace("home_stage_", "")
    is_backdated = "backdated" in user_states.get(user_id, {}).get("step", "")
    
    user_data[user_id]["home_stage"] = stage
    user_data[user_id]["stage"] = stage
    user_data[user_id]["stage_name"] = STAGE_NAMES.get(stage, stage)
    user_states[user_id] = {"step": "home_grade_backdated" if is_backdated else "home_grade"}
    
    await bot.send_message(
        chat_id=event.message.recipient.chat_id,
        text=f"✅ Ступень: {STAGE_NAMES.get(stage)}\n\n🏠 **Выберите класс:**",
        attachments=[home_grade_menu(stage)]
    )
    await event.answer()

@dp.message_callback(F.callback.payload == "back_to_home_stage")
async def back_to_home_stage(event: MessageCallback):
    user_id = event.callback.user.user_id
    is_backdated = "backdated" in user_states.get(user_id, {}).get("step", "")
    user_states[user_id] = {"step": "home_stage_backdated" if is_backdated else "home_stage"}
    await bot.send_message(
        chat_id=event.message.recipient.chat_id,
        text="🏠 **Выберите ступень:**",
        attachments=[stage_menu_home()]
    )
    await event.answer()

@dp.message_callback(F.callback.payload.startswith("home_grade_"))
async def select_home_grade(event: MessageCallback):
    user_id = event.callback.user.user_id
    grade = event.callback.payload.replace("home_grade_", "")
    class_name = grade
    user_data[user_id]["class_name"] = class_name
    is_backdated = "backdated" in user_states.get(user_id, {}).get("step", "")
    user_states[user_id] = {"step": "category_backdated" if is_backdated else "category"}
    
    stage = user_data[user_id].get("stage", "2")
    await bot.send_message(
        chat_id=event.message.recipient.chat_id,
        text=f"✅ Класс: {class_name}\n\n🍽️ **Выберите категорию питания:**",
        attachments=[category_menu(stage)]
    )
    await event.answer()

# ========== ВЫБОР СТУПЕНИ ==========
@dp.message_callback(F.callback.payload.startswith("stage_"))
async def select_stage(event: MessageCallback):
    user_id = event.callback.user.user_id
    stage = event.callback.payload.replace("stage_", "")
    user_data[user_id]["stage"] = stage
    user_data[user_id]["stage_name"] = STAGE_NAMES.get(stage, stage)
    is_backdated = "backdated" in user_states.get(user_id, {}).get("step", "")
    user_states[user_id] = {"step": "grade_backdated" if is_backdated else "grade"}
    await bot.send_message(chat_id=event.message.recipient.chat_id,
                           text=f"✅ Ступень: {STAGE_NAMES.get(stage)}\n\n🎓 Выберите класс:",
                           attachments=[grade_menu(stage)])
    await event.answer()

@dp.message_callback(F.callback.payload == "back_to_stage")
async def back_to_stage(event: MessageCallback):
    user_id = event.callback.user.user_id
    is_backdated = "backdated" in user_states.get(user_id, {}).get("step", "")
    user_states[user_id] = {"step": "stage_backdated" if is_backdated else "stage"}
    await bot.send_message(chat_id=event.message.recipient.chat_id, text="📚 Выберите ступень:",
                           attachments=[stage_menu()])
    await event.answer()

# ========== ВЫБОР КЛАССА ==========
@dp.message_callback(F.callback.payload.startswith("grade_"))
async def select_grade(event: MessageCallback):
    user_id = event.callback.user.user_id
    grade = event.callback.payload.replace("grade_", "")
    user_data[user_id]["grade"] = grade
    is_backdated = "backdated" in user_states.get(user_id, {}).get("step", "")
    user_states[user_id] = {"step": "litera_backdated" if is_backdated else "litera"}
    stage = user_data[user_id].get("stage", "2")
    await bot.send_message(chat_id=event.message.recipient.chat_id, text=f"✅ Класс: {grade}\n\n🔤 Выберите литеру:",
                           attachments=[litera_menu(grade, stage)])
    await event.answer()

@dp.message_callback(F.callback.payload == "back_to_grade")
async def back_to_grade(event: MessageCallback):
    user_id = event.callback.user.user_id
    is_backdated = "backdated" in user_states.get(user_id, {}).get("step", "")
    stage = user_data[user_id].get("stage", "2")
    user_states[user_id] = {"step": "grade_backdated" if is_backdated else "grade"}
    await bot.send_message(chat_id=event.message.recipient.chat_id, text="🎓 Выберите класс:",
                           attachments=[grade_menu(stage)])
    await event.answer()

# ========== ВЫБОР ЛИТЕРЫ ==========
@dp.message_callback(F.callback.payload.startswith("class_"))
async def select_litera(event: MessageCallback):
    user_id = event.callback.user.user_id
    parts = event.callback.payload.split("_")
    grade = parts[1]
    litera = parts[2]
    class_name = f"{grade}.{litera}"
    user_data[user_id]["litera"] = litera
    user_data[user_id]["class_name"] = class_name
    is_backdated = "backdated" in user_states.get(user_id, {}).get("step", "")
    user_states[user_id] = {"step": "category_backdated" if is_backdated else "category"}
    stage = user_data[user_id].get("stage", "2")
    await bot.send_message(chat_id=event.message.recipient.chat_id,
                           text=f"✅ Класс: {class_name}\n\n🍽️ Выберите категорию:", attachments=[category_menu(stage)])
    await event.answer()

# ========== ВЫБОР КАТЕГОРИИ ==========
@dp.message_callback(F.callback.payload.startswith("cat_"))
async def select_category(event: MessageCallback):
    user_id = event.callback.user.user_id
    category = event.callback.payload.replace("cat_", "")
    user_data[user_id]["temp_category"] = category
    user_states[user_id] = {"step": "waiting_quantity"}
    await bot.send_message(chat_id=event.message.recipient.chat_id, 
                          text=f"📌 **{category}**\n\n➕ Введите количество учеников (1-100):")
    await event.answer()

@dp.message_callback(F.callback.payload == "back_to_categories")
async def back_to_categories(event: MessageCallback):
    user_id = event.callback.user.user_id
    if user_id not in user_data:
        user_data[user_id] = {"categories": {}}
    stage = user_data[user_id].get("stage", "2")
    is_backdated = "backdated" in user_states.get(user_id, {}).get("step", "")
    user_states[user_id] = {"step": "category_backdated" if is_backdated else "category"}
    await bot.send_message(chat_id=event.message.recipient.chat_id, text="🍽️ Выберите категорию:",
                           attachments=[category_menu(stage)])
    await event.answer()

@dp.message_callback(F.callback.payload.startswith("qty_"))
async def select_quantity(event: MessageCallback):
    user_id = event.callback.user.user_id
    qty_str = event.callback.payload.replace("qty_", "")

    if qty_str == "other":
        user_states[user_id] = {"step": "waiting_quantity"}
        await bot.send_message(chat_id=event.message.recipient.chat_id, text="➕ Введите количество (1-100):")
        await event.answer()
        return

    qty = int(qty_str)
    category = user_data[user_id].get("temp_category")
    class_name = user_data[user_id].get("class_name")

    if "categories" not in user_data[user_id]:
        user_data[user_id]["categories"] = {}
    if class_name not in user_data[user_id]["categories"]:
        user_data[user_id]["categories"][class_name] = {}

    user_data[user_id]["categories"][class_name][category] = qty
    user_data[user_id].pop("temp_category", None)
    
    is_backdated = "backdated" in user_states.get(user_id, {}).get("step", "")
    user_states[user_id] = {"step": "category_backdated" if is_backdated else "category"}

    stage = user_data[user_id].get("stage", "2")
    await bot.send_message(chat_id=event.message.recipient.chat_id,
                           text=f"✅ Добавлено: {category} - {qty} чел.\n\nВыберите следующую категорию или завершите:",
                           attachments=[category_menu(stage)])
    await event.answer()

# ========== ОБРАБОТКА ТЕКСТА ==========
@dp.message_created()
async def handle_text(event: MessageCreated):
    user_id = event.message.sender.user_id
    text = event.message.body.text if event.message.body else None

    if not text or text.startswith('/'):
        return

    if user_id not in user_states:
        await cmd_start(event)
        return

    step = user_states[user_id].get("step")

    if step == "waiting_quantity":
        try:
            qty = int(text.strip())
            if qty < 1 or qty > 100:
                await event.message.answer("❌ Введите число от 1 до 100")
                return

            category = user_data[user_id].get("temp_category")
            class_name = user_data[user_id].get("class_name")

            if "categories" not in user_data[user_id]:
                user_data[user_id]["categories"] = {}
            if class_name not in user_data[user_id]["categories"]:
                user_data[user_id]["categories"][class_name] = {}

            user_data[user_id]["categories"][class_name][category] = qty
            user_data[user_id].pop("temp_category", None)
            
            is_backdated = "backdated" in user_states.get(user_id, {}).get("step", "")
            user_states[user_id] = {"step": "category_backdated" if is_backdated else "category"}

            stage = user_data[user_id].get("stage", "2")
            await event.message.answer(f"✅ Добавлено: {category} - {qty} чел.\n\nВыберите следующую категорию или завершите:",
                                       attachments=[category_menu(stage)])
        except ValueError:
            await event.message.answer("❌ Введите число")
    
    elif step in ["after_school_class", "after_school_class_backdated"]:
        class_name = text.strip()
        if len(class_name) < 1:
            await event.message.answer("❌ Введите название класса (например: 1.5, 1.2)")
            return
        
        if "categories" not in user_data[user_id]:
            user_data[user_id]["categories"] = {}
        user_data[user_id]["class_name"] = class_name
        user_states[user_id] = {"step": "after_school_quantity"}
        
        await event.message.answer(
            f"✅ Класс: {class_name}\n\n➕ **Введите количество учеников на продленку (1-100):**"
        )
    
    elif step == "after_school_quantity":
        try:
            qty = int(text.strip())
            if qty < 1 or qty > 100:
                await event.message.answer("❌ Введите число от 1 до 100")
                return
            
            building = user_data[user_id]["building"]
            class_name = user_data[user_id]["class_name"]
            teacher_name = event.message.sender.first_name or "Администратор"
            is_backdated = "backdated" in user_states.get(user_id, {}).get("step", "")
            back_date = user_data[user_id].get("back_date") if is_backdated else None
            
            if back_date:
                # Подача задним числом
                add_meal_backdated(building, "after_school", "", "", class_name, "Продленка", qty, teacher_name, user_id, back_date)
                date_display = datetime.strptime(back_date, "%Y-%m-%d").strftime("%d.%m.%Y")
                date_note = f"(задним числом за {date_display})"
            else:
                add_meal(building, "after_school", "", "", class_name, "Продленка", qty, teacher_name, user_id)
                date_display = datetime.now().strftime("%d.%m.%Y")
                date_note = ""
            
            group_chat_id = BUILDING_1_CHAT_ID if building == "Марченко" else BUILDING_2_CHAT_ID
            group_msg = f"""⏰ **{'ЗАЯВКА ЗАДНИМ ЧИСЛОМ' if back_date else 'НОВАЯ ЗАЯВКА НА ПРОДЛЕНКУ'}**

📅 **Дата:** {date_display}
🏫 **Здание:** {building}
👤 **Учитель:** {teacher_name}
📖 **Класс:** {class_name}
🍽️ **Количество:** {qty} чел.
{date_note}"""
            
            if group_chat_id != 0:
                try:
                    await bot.send_message(chat_id=group_chat_id, text=group_msg)
                except Exception as e:
                    print(f"Ошибка отправки в группу: {e}")
            
            await event.message.answer(
                f"✅ **Заявка на продленку {'задним числом ' if back_date else ''}принята!**\n\n"
                f"📅 **Дата:** {date_display}\n"
                f"🏫 **Здание:** {building}\n"
                f"📖 **Класс:** {class_name}\n"
                f"🍽️ **Количество:** {qty} чел.",
                attachments=[admin_menu() if is_admin_group(event.message.recipient.chat_id) else main_menu()]
            )
            
            user_states.pop(user_id, None)
            user_data.pop(user_id, None)
            
        except ValueError:
            await event.message.answer("❌ Введите число")
    
    elif user_states[user_id].get("edit_waiting_qty"):
        try:
            qty = int(text.strip())
            if qty < 0 or qty > 100:
                await event.message.answer("❌ Введите число от 0 до 100")
                return
            
            category = user_states[user_id].get("edit_temp_category")
            user_states[user_id]["edit_categories"][category] = qty
            user_states[user_id].pop("edit_temp_category", None)
            user_states[user_id].pop("edit_waiting_qty", None)
            
            stage = user_states[user_id]["stage"]
            await event.message.answer(
                f"✅ Установлено: {category} - {qty} чел.\n\nПродолжить редактирование:",
                attachments=[edit_category_menu(user_states[user_id]["edit_categories"], stage)]
            )
        except ValueError:
            await event.message.answer("❌ Введите число")
    else:
        await cmd_start(event)

# ========== ЗАВЕРШЕНИЕ ЗАЯВКИ ==========
@dp.message_callback(F.callback.payload == "finish_request")
async def finish_request(event: MessageCallback):
    user_id = event.callback.user.user_id

    if user_id not in user_data:
        await bot.send_message(chat_id=event.message.recipient.chat_id, text="❌ Нет данных для заявки")
        await event.answer()
        return

    data = user_data[user_id]
    class_name = data.get("class_name", "")
    categories_dict = data.get("categories", {}).get(class_name, {})

    if not categories_dict:
        await bot.send_message(chat_id=event.message.recipient.chat_id, text="❌ Не добавлено ни одной категории!",
                               attachments=[category_menu(data.get("stage", "2"))])
        await event.answer()
        return

    total = sum(categories_dict.values())
    building = data.get("building", "")
    stage_name = data.get("stage_name", "")
    back_date = data.get("back_date")

    msg = "📝 **ПРОВЕРЬТЕ ЗАЯВКУ:**\n\n"
    if back_date:
        date_display = datetime.strptime(back_date, "%Y-%m-%d").strftime("%d.%m.%Y")
        msg += f"📅 **Дата:** {date_display} (задним числом)\n"
    msg += f"🏫 **Здание:** {building}\n"
    msg += f"📚 **Ступень:** {stage_name}\n"
    msg += f"📖 **Класс:** {class_name}\n\n"
    msg += "📊 **Состав заявки:**\n"

    for cat, qty in categories_dict.items():
        if qty > 0:
            msg += f"   • {cat}: {qty} чел.\n"

    msg += f"\n🍽️ **ВСЕГО:** {total} чел.\n\n✅ Всё верно?"

    user_states[user_id] = {"step": "confirm"}
    await bot.send_message(chat_id=event.message.recipient.chat_id, text=msg, attachments=[confirm_menu()])
    await event.answer()

# ========== ПОДТВЕРЖДЕНИЕ ЗАЯВКИ ==========
@dp.message_callback(F.callback.payload == "confirm_submit")
async def confirm_submit(event: MessageCallback):
    user_id = event.callback.user.user_id

    if user_id not in user_data:
        await event.answer(notification="❌ Нет данных для заявки")
        return

    data = user_data[user_id]
    now = datetime.now()
    back_date = data.get("back_date")
    
    if back_date:
        date_display = datetime.strptime(back_date, "%Y-%m-%d").strftime("%d.%m.%Y")
        date_for_save = back_date
        is_backdated = True
    else:
        date_display = now.strftime("%d.%m.%Y")
        date_for_save = now.strftime("%Y-%m-%d")
        is_backdated = False

    teacher_fullname = event.callback.user.first_name or "Администратор"
    if event.callback.user.last_name:
        teacher_fullname = f"{event.callback.user.first_name} {event.callback.user.last_name}"
    if event.callback.user.username:
        teacher_fullname = f"{teacher_fullname} (@{event.callback.user.username})"

    building = data.get("building", "")
    stage = data.get("stage", "")
    stage_name = data.get("stage_name", "")
    grade = data.get("grade", "")
    litera = data.get("litera", "")
    class_name = data.get("class_name", "")
    categories_dict = data.get("categories", {}).get(class_name, {})

    # Проверка на дубли для задних чисел
    if is_backdated:
        if has_user_request_on_date(user_id, building, class_name, stage, date_for_save):
            error_text = f"❌ **На {date_display} уже есть заявка для класса {class_name}!**\n\n"
            error_text += f"💡 Используйте функцию редактирования для изменения существующей заявки."
            
            await bot.send_message(
                chat_id=event.message.recipient.chat_id,
                text=error_text
            )
            user_states.pop(user_id, None)
            user_data.pop(user_id, None)
            await event.answer(notification="❌ Заявка отклонена")
            return
    else:
        if has_user_today_request(user_id, building, class_name, stage):
            if stage == "after_school":
                error_text = f"❌ **Вы уже подавали заявку на продленку для класса {class_name} сегодня!**\n\n"
            else:
                error_text = f"❌ **Вы уже подавали заявку на питание для класса {class_name} сегодня!**\n\n"
            
            error_text += f"📅 Дата: {date_display}\n"
            error_text += f"🏫 Здание: {building}\n\n"
            error_text += f"💡 Если нужно изменить заявку, используйте функцию редактирования у администратора."
            
            await bot.send_message(
                chat_id=event.message.recipient.chat_id,
                text=error_text
            )
            user_states.pop(user_id, None)
            user_data.pop(user_id, None)
            await event.answer(notification="❌ Заявка отклонена")
            return

    # Сохраняем заявку
    for category, quantity in categories_dict.items():
        if quantity > 0:
            if is_backdated:
                add_meal_backdated(building, stage, grade, litera, class_name, category, quantity, teacher_fullname, user_id, date_for_save)
            else:
                add_meal(building, stage, grade, litera, class_name, category, quantity, teacher_fullname, user_id)

    total = sum(categories_dict.values())
    categories_text = ""
    for cat, qty in categories_dict.items():
        if qty > 0:
            categories_text += f"   • {cat}: {qty} чел.\n"

    # Определяем группу для отправки уведомления
    if building == "Надомное":
        group_chat_id = BUILDING_1_CHAT_ID
        building_display = "Надомное отделение (Марченко)"
    elif stage == "after_school":
        group_chat_id = BUILDING_1_CHAT_ID if building == "Марченко" else BUILDING_2_CHAT_ID
        building_display = f"Продленка ({building})"
    else:
        building_display = building
        group_chat_id = BUILDING_1_CHAT_ID if building == "Марченко" else BUILDING_2_CHAT_ID

    backdated_note = " (ЗАДНИМ ЧИСЛОМ)" if is_backdated else ""
    group_msg = f"""🍽️ **{'ЗАЯВКА ЗАДНИМ ЧИСЛОМ' if is_backdated else 'НОВАЯ ЗАЯВКА НА ПИТАНИЕ'}**

📅 **Дата:** {date_display}
🏫 **Здание:** {building_display}
👤 **Учитель:** {teacher_fullname}
📖 **Класс:** {class_name}
📚 **Ступень:** {stage_name}

📊 **Состав заявки:**
{categories_text}
🍽️ **ВСЕГО: {total} чел.**{backdated_note}"""

    if group_chat_id != 0:
        try:
            await bot.send_message(chat_id=group_chat_id, text=group_msg)
        except Exception as e:
            print(f"Ошибка отправки в группу: {e}")

    answer_msg = f"✅ **Заявка {'задним числом ' if is_backdated else ''}принята!**\n\n"
    answer_msg += f"📅 **Дата:** {date_display}\n"
    answer_msg += f"🏫 **Здание:** {building_display}\n"
    answer_msg += f"👤 **Учитель:** {teacher_fullname}\n"
    answer_msg += f"📖 **Класс:** {class_name}\n\n"
    answer_msg += f"📊 **Подано:**\n{categories_text}\n"
    answer_msg += f"🍽️ **ВСЕГО: {total} чел.**"

    menu = admin_menu() if is_admin_group(event.message.recipient.chat_id) else main_menu()
    await bot.send_message(chat_id=event.message.recipient.chat_id, text=answer_msg, attachments=[menu])

    user_states.pop(user_id, None)
    user_data.pop(user_id, None)
    await event.answer(notification="✅ Заявка отправлена!")

# ========== МОИ ЗАЯВКИ (СЕГОДНЯ) ==========
@dp.message_callback(F.callback.payload == "my_requests")
async def my_requests(event: MessageCallback):
    user_id = event.callback.user.user_id
    meals = get_user_meals_today(user_id)

    if not meals:
        text = "📭 У вас пока нет заявок на сегодня"
    else:
        text = "📋 **ВАШИ ЗАЯВКИ НА СЕГОДНЯ:**\n\n"
        for meal in meals:
            stage_display = ""
            if meal.get("stage") == "home":
                stage_display = " 🏠"
            elif meal.get("stage") == "after_school":
                stage_display = " ⏰"
            text += f"🏫 {meal.get('building')} | 📖 {meal.get('class_name')}{stage_display}\n"
            text += f"   • {meal.get('category')}: {meal.get('quantity')} чел.\n\n"

    menu = admin_menu() if is_admin_group(event.message.recipient.chat_id) else main_menu()
    await bot.send_message(chat_id=event.message.recipient.chat_id, text=text, attachments=[menu])
    await event.answer()

# ========== МОИ ЗАЯВКИ ЗА МЕСЯЦ (УЧИТЕЛЬ) ==========
@dp.message_callback(F.callback.payload == "my_requests_by_month")
async def my_requests_by_month(event: MessageCallback):
    user_id = event.callback.user.user_id
    user_states[user_id] = {"view_type": "user_month"}
    
    await bot.send_message(
        chat_id=event.message.recipient.chat_id,
        text="📅 **Выберите месяц для просмотра ваших заявок:**",
        attachments=[month_menu_teacher()]
    )
    await event.answer()

# ========== КТО ПОДАЛ ЗАЯВКУ ПО СМЕНАМ (АДМИН) ==========
@dp.message_callback(F.callback.payload == "view_requests_by_shiftt")
async def view_requests_by_shift(event: MessageCallback):
    if not is_admin_group(event.message.recipient.chat_id):
        await event.answer(notification="❌ Доступно только в группе администраторов")
        return
    
    await bot.send_message(
        chat_id=event.message.recipient.chat_id,
        text="👥 **Выберите смену:**",
        attachments=[shift_menu()]
    )
    await event.answer()

@dp.message_callback(F.callback.payload.startswith("shift_"))
async def show_shift_requests(event: MessageCallback):
    if not is_admin_group(event.message.recipient.chat_id):
        await event.answer(notification="❌ Доступно только в группе администраторов")
        return
    
    shift = int(event.callback.payload.replace("shift_", ""))
    building = get_admin_building(event.message.recipient.chat_id)
    
    if not building:
        await event.answer(notification="❌ Не удалось определить здание")
        return
    
    today = datetime.now().strftime("%Y-%m-%d")
    today_display = datetime.now().strftime("%d.%m.%Y")
    
    await bot.send_message(
        chat_id=event.message.recipient.chat_id,
        text=f"⏳ Загружаю заявки для {building}, {shift} смена..."
    )
    
    requests = get_requests_by_shift(building, shift, today)
    result_text = format_requests_by_shift(requests, shift, building, today_display)
    
    if len(result_text) > 4000:
        total = sum(req["quantity"] for req in requests)
        await bot.send_message(
            chat_id=event.message.recipient.chat_id,
            text=f"📋 Заявки для {building}, {shift} смена на {today_display}\n\n✅ Всего классов: {len(set(r['class_name'] for r in requests))}\n🍽️ Всего порций: {total}",
            attachments=[shift_menu()]
        )
    else:
        await bot.send_message(
            chat_id=event.message.recipient.chat_id,
            text=result_text,
            attachments=[shift_menu()]
        )
    
    await event.answer()

# ========== РЕДАКТИРОВАНИЕ ЗАЯВКИ (АДМИН) ==========
@dp.message_callback(F.callback.payload == "edit_request")
async def edit_request_start(event: MessageCallback):
    if not is_admin_group(event.message.recipient.chat_id):
        await event.answer(notification="❌ Доступно только в группе администраторов")
        return
    
    building = get_admin_building(event.message.recipient.chat_id)
    if not building:
        await event.answer(notification="❌ Не удалось определить здание")
        return
    
    # Получаем заявки за последние 3 дня
    requests = get_requests_for_last_days(building, days=3)
    
    if not requests:
        await bot.send_message(
            chat_id=event.message.recipient.chat_id,
            text=f"📭 Нет заявок для {building} за последние 3 дня",
            attachments=[admin_menu()]
        )
        await event.answer()
        return
    
    # Группируем по датам
    from collections import defaultdict
    requests_by_date = defaultdict(list)
    for req in requests:
        requests_by_date[req["date"]].append(req)
    
    # Показываем меню выбора даты
    buttons = []
    for date in sorted(requests_by_date.keys(), reverse=True):
        date_display = datetime.strptime(date, "%Y-%m-%d").strftime("%d.%m.%Y")
        count = len(requests_by_date[date])
        buttons.append([CallbackButton(text=f"📅 {date_display} ({count} заявок)", payload=f"edit_date_{date}", intent=Intent.DEFAULT)])
    
    buttons.append([CallbackButton(text="◀️ Назад", payload="back_to_admin_menu", intent=Intent.DEFAULT)])
    buttons.append([CallbackButton(text="❌ Отмена", payload="cancel", intent=Intent.NEGATIVE)])
    
    from maxapi.types import ButtonsPayload, Attachment
    await bot.send_message(
        chat_id=event.message.recipient.chat_id,
        text=f"✏️ **Редактирование заявок**\n🏫 {building}\n\nВыберите дату:",
        attachments=[Attachment(type="inline_keyboard", payload=ButtonsPayload(buttons=buttons))]
    )
    await event.answer()

@dp.message_callback(F.callback.payload.startswith("edit_date_"))
async def edit_date_selected(event: MessageCallback):
    if not is_admin_group(event.message.recipient.chat_id):
        await event.answer(notification="❌ Доступно только в группе администраторов")
        return
    
    date = event.callback.payload.replace("edit_date_", "")
    building = get_admin_building(event.message.recipient.chat_id)
    
    requests = get_requests_for_last_days(building, days=3)
    requests = [r for r in requests if r["date"] == date]
    
    date_display = datetime.strptime(date, "%Y-%m-%d").strftime("%d.%m.%Y")
    
    from maxapi.types import ButtonsPayload, Attachment
    buttons = []
    for req in requests:
        buttons.append([CallbackButton(text=f"📖 {req['class_name']} (👤 {req['teacher_name']})", payload=f"edit_class_date_{date}_{req['class_name']}", intent=Intent.DEFAULT)])
    
    buttons.append([CallbackButton(text="◀️ Назад", payload="edit_request", intent=Intent.DEFAULT)])
    buttons.append([CallbackButton(text="❌ Отмена", payload="cancel", intent=Intent.NEGATIVE)])
    
    await bot.send_message(
        chat_id=event.message.recipient.chat_id,
        text=f"✏️ **Редактирование заявок**\n🏫 {building}\n📅 {date_display}\n\nВыберите класс:",
        attachments=[Attachment(type="inline_keyboard", payload=ButtonsPayload(buttons=buttons))]
    )
    await event.answer()

@dp.message_callback(F.callback.payload.startswith("edit_class_date_"))
async def edit_class_date_selected(event: MessageCallback):
    if not is_admin_group(event.message.recipient.chat_id):
        await event.answer(notification="❌ Доступно только в группе администраторов")
        return
    
    parts = event.callback.payload.replace("edit_class_date_", "").split("_")
    date = parts[0]
    class_name = "_".join(parts[1:])
    
    building = get_admin_building(event.message.recipient.chat_id)
    
    # Получаем данные заявки
    current_request = get_request_by_date(building, class_name, date)
    
    # Получаем информацию об учителе
    conn = sqlite3.connect("meals.db")
    cursor = conn.execute("""
        SELECT DISTINCT teacher_id, teacher_name, stage
        FROM meals 
        WHERE building = ? AND date = ? AND class_name = ?
        LIMIT 1
    """, (building, date, class_name))
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        await bot.send_message(
            chat_id=event.message.recipient.chat_id,
            text="❌ Заявка не найдена",
            attachments=[admin_menu()]
        )
        await event.answer()
        return
    
    teacher_id, teacher_name, stage = result
    
    user_states[event.callback.user.user_id] = {
        "edit_mode": True,
        "edit_date": date,
        "building": building,
        "class_name": class_name,
        "teacher_id": teacher_id,
        "teacher_name": teacher_name,
        "stage": stage,
        "edit_categories": current_request["categories"].copy()
    }
    
    await bot.send_message(
        chat_id=event.message.recipient.chat_id,
        text=f"✏️ **Редактирование заявки**\n"
             f"📅 Дата: {datetime.strptime(date, '%Y-%m-%d').strftime('%d.%m.%Y')}\n"
             f"🏫 {building}\n"
             f"👤 {teacher_name}\n"
             f"📖 {class_name}\n\n"
             f"Выберите категорию для изменения:",
        attachments=[edit_category_menu(user_states[event.callback.user.user_id]["edit_categories"], stage)]
    )
    await event.answer()

@dp.message_callback(F.callback.payload.startswith("edit_cat_"))
async def edit_category_selected(event: MessageCallback):
    if not is_admin_group(event.message.recipient.chat_id):
        await event.answer(notification="❌ Доступно только в группе администраторов")
        return
    
    category = event.callback.payload.replace("edit_cat_", "")
    user_id = event.callback.user.user_id
    
    current_qty = user_states[user_id]["edit_categories"].get(category, 0)
    user_states[user_id]["edit_temp_category"] = category
    
    await bot.send_message(
        chat_id=event.message.recipient.chat_id,
        text=f"📌 **{category}**\nТекущее значение: {current_qty} чел.\n\nВыберите новое количество:",
        attachments=[edit_quantity_menu(category, current_qty)]
    )
    await event.answer()

@dp.message_callback(F.callback.payload.startswith("edit_qty_"))
async def edit_quantity_selected(event: MessageCallback):
    if not is_admin_group(event.message.recipient.chat_id):
        await event.answer(notification="❌ Доступно только в группе администраторов")
        return
    
    qty_str = event.callback.payload.replace("edit_qty_", "")
    user_id = event.callback.user.user_id
    category = user_states[user_id].get("edit_temp_category")
    
    if qty_str == "other":
        user_states[user_id]["edit_waiting_qty"] = True
        await bot.send_message(
            chat_id=event.message.recipient.chat_id,
            text="➕ Введите количество учеников (1-100):"
        )
        await event.answer()
        return
    
    qty = int(qty_str)
    user_states[user_id]["edit_categories"][category] = qty
    user_states[user_id].pop("edit_temp_category", None)
    user_states[user_id].pop("edit_waiting_qty", None)
    
    stage = user_states[user_id]["stage"]
    await bot.send_message(
        chat_id=event.message.recipient.chat_id,
        text=f"✅ Установлено: {category} - {qty} чел.\n\nПродолжить редактирование:",
        attachments=[edit_category_menu(user_states[user_id]["edit_categories"], stage)]
    )
    await event.answer()

@dp.message_callback(F.callback.payload == "edit_save")
async def edit_save(event: MessageCallback):
    if not is_admin_group(event.message.recipient.chat_id):
        await event.answer(notification="❌ Доступно только в группе администраторов")
        return
    
    user_id = event.callback.user.user_id
    state = user_states.get(user_id, {})
    
    if not state.get("edit_mode"):
        await event.answer(notification="❌ Нет активного редактирования")
        return
    
    building = state["building"]
    class_name = state["class_name"]
    teacher_id = state["teacher_id"]
    teacher_name = state["teacher_name"]
    new_categories = state["edit_categories"]
    edit_date = state.get("edit_date", datetime.now().strftime("%Y-%m-%d"))
    
    # Обновляем заявку на указанную дату
    update_user_request_on_date(teacher_id, building, class_name, new_categories, teacher_name, edit_date)
    
    total = sum(new_categories.values())
    categories_text = "\n".join([f"   • {cat}: {qty} чел." for cat, qty in new_categories.items() if qty > 0])
    date_display = datetime.strptime(edit_date, "%Y-%m-%d").strftime("%d.%m.%Y")
    
    await bot.send_message(
        chat_id=event.message.recipient.chat_id,
        text=f"✅ **Заявка обновлена!**\n\n"
             f"📅 Дата: {date_display}\n"
             f"🏫 {building}\n"
             f"👤 {teacher_name}\n"
             f"📖 {class_name}\n\n"
             f"📊 **Новый состав:**\n{categories_text}\n\n"
             f"🍽️ **ВСЕГО: {total} чел.**",
        attachments=[admin_menu()]
    )
    
    # Отправляем уведомление
    group_chat_id = BUILDING_1_CHAT_ID if building == "Марченко" else BUILDING_2_CHAT_ID
    if group_chat_id != 0:
        notify_msg = f"✏️ **ЗАЯВКА ИЗМЕНЕНА**\n\n📅 {date_display}\n🏫 {building}\n👤 {teacher_name}\n📖 {class_name}\n\n📊 **Новый состав:**\n{categories_text}\n\n🍽️ **ВСЕГО: {total} чел.**"
        try:
            await bot.send_message(chat_id=group_chat_id, text=notify_msg)
        except:
            pass
    
    user_states.pop(user_id, None)
    await event.answer()

@dp.message_callback(F.callback.payload == "edit_delete")
async def edit_delete(event: MessageCallback):
    if not is_admin_group(event.message.recipient.chat_id):
        await event.answer(notification="❌ Доступно только в группе администраторов")
        return
    
    user_id = event.callback.user.user_id
    state = user_states.get(user_id, {})
    
    if not state.get("edit_mode"):
        await event.answer(notification="❌ Нет активного редактирования")
        return
    
    building = state["building"]
    class_name = state["class_name"]
    teacher_id = state["teacher_id"]
    teacher_name = state["teacher_name"]
    edit_date = state.get("edit_date", datetime.now().strftime("%Y-%m-%d"))
    
    from storage_food import delete_user_request_by_date
    delete_user_request_by_date(teacher_id, building, class_name, edit_date)
    
    date_display = datetime.strptime(edit_date, "%Y-%m-%d").strftime("%d.%m.%Y")
    
    await bot.send_message(
        chat_id=event.message.recipient.chat_id,
        text=f"❌ **Заявка удалена!**\n\n"
             f"📅 Дата: {date_display}\n"
             f"🏫 {building}\n"
             f"👤 {teacher_name}\n"
             f"📖 {class_name}",
        attachments=[admin_menu()]
    )
    
    group_chat_id = BUILDING_1_CHAT_ID if building == "Марченко" else BUILDING_2_CHAT_ID
    if group_chat_id != 0:
        notify_msg = f"❌ **ЗАЯВКА ОТМЕНЕНА**\n\n📅 {date_display}\n🏫 {building}\n👤 {teacher_name}\n📖 {class_name}"
        try:
            await bot.send_message(chat_id=group_chat_id, text=notify_msg)
        except:
            pass
    
    user_states.pop(user_id, None)
    await event.answer()

@dp.message_callback(F.callback.payload == "back_to_edit_class")
async def back_to_edit_class(event: MessageCallback):
    await edit_request_start(event)

# ========== ВСЕ ЗАЯВКИ ПО КЛАССУ (АДМИН) ==========
@dp.message_callback(F.callback.payload == "all_requests_by_class")
async def all_requests_by_class_start(event: MessageCallback):
    if not is_admin_group(event.message.recipient.chat_id):
        await event.answer(notification="❌ Доступно только в группе администраторов")
        return
    
    await bot.send_message(
        chat_id=event.message.recipient.chat_id,
        text="📅 **Выберите месяц для просмотра заявок:**",
        attachments=[month_menu_admin()]
    )
    await event.answer()

# ========== ОБЩИЙ ОБРАБОТЧИК ВЫБОРА МЕСЯЦА ==========
@dp.message_callback(F.callback.payload.startswith("month_"))
async def select_month_global(event: MessageCallback):
    user_id = event.callback.user.user_id
    month = int(event.callback.payload.replace("month_", ""))
    year = datetime.now().year
    
    view_type = user_states.get(user_id, {}).get("view_type", "admin")
    
    if view_type == "user_month":
        requests_data = get_user_requests_by_month(user_id, month, year)
        user_name = event.callback.user.first_name or "Учитель"
        if event.callback.user.last_name:
            user_name = f"{event.callback.user.first_name} {event.callback.user.last_name}"
        
        result_text = format_user_requests_by_month(requests_data, month, year, user_name)
        
        if len(result_text) > 4000:
            await bot.send_message(
                chat_id=event.message.recipient.chat_id,
                text=f"📅 Ваши заявки за {datetime(year, month, 1).strftime('%B %Y')}\n\nСлишком много данных.",
                attachments=[main_menu()]
            )
        else:
            await bot.send_message(
                chat_id=event.message.recipient.chat_id,
                text=result_text,
                attachments=[main_menu()]
            )
        user_states.pop(user_id, None)
    else:
        if not is_admin_group(event.message.recipient.chat_id):
            await event.answer(notification="❌ Доступно только в группе администраторов")
            return
        
        building = get_admin_building(event.message.recipient.chat_id)
        if not building:
            await event.answer(notification="❌ Не удалось определить здание")
            return
        
        user_states[user_id] = {
            "view_month": month,
            "view_year": year,
            "view_building": building,
            "view_type": "admin_class"
        }
        
        classes = get_all_classes_with_requests(building, month, year)
        
        if not classes:
            month_name = datetime(year, month, 1).strftime("%B %Y")
            await bot.send_message(
                chat_id=event.message.recipient.chat_id,
                text=f"📭 Нет заявок за {month_name} в здании {building}",
                attachments=[admin_menu()]
            )
        else:
            await bot.send_message(
                chat_id=event.message.recipient.chat_id,
                text=f"📋 **Выберите класс**\n🏫 {building}\n📅 {datetime(year, month, 1).strftime('%B %Y')}\n\nКлассы с заявками:",
                attachments=[class_selection_menu(classes)]
            )
    
    await event.answer()

@dp.message_callback(F.callback.payload.startswith("view_class_"))
async def show_class_requests_admin(event: MessageCallback):
    if not is_admin_group(event.message.recipient.chat_id):
        await event.answer(notification="❌ Доступно только в группе администраторов")
        return
    
    class_name = event.callback.payload.replace("view_class_", "")
    user_id = event.callback.user.user_id
    state = user_states.get(user_id, {})
    
    building = state.get("view_building", get_admin_building(event.message.recipient.chat_id))
    month = state.get("view_month", datetime.now().month)
    year = state.get("view_year", datetime.now().year)
    
    await bot.send_message(
        chat_id=event.message.recipient.chat_id,
        text=f"⏳ Загружаю заявки для класса {class_name}..."
    )
    
    requests_data = get_all_requests_by_class(building, class_name, month, year)
    result_text = format_all_requests_by_class(building, class_name, requests_data, month, year)
    
    if len(result_text) > 4000:
        await bot.send_message(
            chat_id=event.message.recipient.chat_id,
            text=f"📋 Заявки для {class_name} за {datetime(year, month, 1).strftime('%B %Y')}\n\nСлишком много данных.",
            attachments=[admin_menu()]
        )
    else:
        await bot.send_message(
            chat_id=event.message.recipient.chat_id,
            text=result_text,
            attachments=[admin_menu()]
        )
    
    user_states.pop(user_id, None)
    await event.answer()

@dp.message_callback(F.callback.payload == "back_to_month_selection")
async def back_to_month_selection(event: MessageCallback):
    await all_requests_by_class_start(event)

@dp.message_callback(F.callback.payload == "back_to_main_menu")
async def back_to_main_menu(event: MessageCallback):
    await cmd_start(event)
    await event.answer()

# ========== ОТЧЁТЫ ==========
@dp.message_callback(F.callback.payload == "make_report")
async def make_report_start(event: MessageCallback):
    if not is_admin_group(event.message.recipient.chat_id):
        await event.answer(notification="❌ Доступно только в группе администраторов")
        return

    await bot.send_message(chat_id=event.message.recipient.chat_id, text="📊 Выберите период отчёта:",
                           attachments=[report_period_menu()])
    await event.answer()

@dp.message_callback(F.callback.payload == "back_to_admin_menu")
async def back_to_admin_menu(event: MessageCallback):
    await bot.send_message(chat_id=event.message.recipient.chat_id, text="🍽️ Бот-Ланчбокс (Администратор)",
                           attachments=[admin_menu()])
    await event.answer()

@dp.message_callback(F.callback.payload.startswith("report_"))
async def generate_report(event: MessageCallback):
    if not is_admin_group(event.message.recipient.chat_id):
        await event.answer(notification="❌ Доступно только в группе администраторов")
        return
    
    period = event.callback.payload.replace("report_", "")
    building = get_admin_building(event.message.recipient.chat_id)
    
    if not building:
        await event.answer(notification="❌ Не удалось определить здание")
        return
    
    now = datetime.now()
    today = now.date()
    
    if period == "daily":
        date_from = now.strftime("%Y-%m-%d")
        date_to = now.strftime("%Y-%m-%d")
        period_type = "daily"
        period_display = "Ежедневный"
        
    elif period == "weekly":
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        
        if start_of_week.month < now.month:
            date_from = today.replace(day=1).strftime("%Y-%m-%d")
        else:
            date_from = start_of_week.strftime("%Y-%m-%d")
        
        if end_of_week.month > now.month:
            if now.month == 12:
                last_day = now.replace(year=now.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                last_day = now.replace(month=now.month + 1, day=1) - timedelta(days=1)
            date_to = last_day.strftime("%Y-%m-%d")
        else:
            date_to = end_of_week.strftime("%Y-%m-%d")
        
        period_type = "weekly"
        period_display = "Еженедельный"
        
    else:
        start_of_month = today.replace(day=1)
        if now.month == 12:
            end_of_month = now.replace(year=now.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            end_of_month = now.replace(month=now.month + 1, day=1) - timedelta(days=1)
        
        date_from = start_of_month.strftime("%Y-%m-%d")
        date_to = end_of_month.strftime("%Y-%m-%d")
        period_type = "monthly"
        period_display = "Ежемесячный"
    
    await bot.send_message(
        chat_id=event.message.recipient.chat_id,
        text=f"📊 Формирую {period_display} отчёт для {building}..."
    )
    
    file_path = create_excel_report_for_building(building, date_from, date_to, period_type)
    
    if file_path and os.path.exists(file_path):
        date_from_display = datetime.strptime(date_from, "%Y-%m-%d").strftime("%d.%m.%Y")
        date_to_display = datetime.strptime(date_to, "%Y-%m-%d").strftime("%d.%m.%Y")
        
        if period == "daily":
            period_text = f"за {date_from_display}"
        elif period == "weekly":
            period_text = f"за период {date_from_display} - {date_to_display}"
        else:
            month_name = now.strftime("%B %Y")
            period_text = f"за {month_name}"
        
        result_message = f"""✅ **{period_display} отчёт для {building} сформирован!**
📅 {period_text}
📧 Отправлен на email администраторов."""
        
        await bot.send_message(chat_id=event.message.recipient.chat_id,
                              text=result_message,
                              attachments=[admin_menu()])
        
        print(f"✅ Отчёт для {building} создан и отправлен на email")
        print(f"   Период: {date_from} - {date_to}")
    else:
        await bot.send_message(chat_id=event.message.recipient.chat_id,
                              text=f"📭 Нет данных для {building} за выбранный период",
                              attachments=[admin_menu()])
    
    await event.answer()

# ========== ОТМЕНА ==========
@dp.message_callback(F.callback.payload == "cancel")
async def cancel_handler(event: MessageCallback):
    user_id = event.callback.user.user_id
    user_states.pop(user_id, None)
    user_data.pop(user_id, None)

    if is_admin_group(event.message.recipient.chat_id):
        await bot.send_message(chat_id=event.message.recipient.chat_id, text="❌ Отменено", attachments=[admin_menu()])
    else:
        await bot.send_message(chat_id=event.message.recipient.chat_id, text="❌ Отменено", attachments=[main_menu()])
    await event.answer()

print("✅ bot_food_max.py загружен")
