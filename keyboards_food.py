# keyboards_food.py
from maxapi.types import CallbackButton, ButtonsPayload, Attachment
from maxapi.enums.intent import Intent

# ========== ГЛАВНОЕ МЕНЮ ДЛЯ УЧИТЕЛЕЙ ==========
def main_menu():
    btn_food = CallbackButton(text="🍽️ Подать заявку", payload="new_food_request", intent=Intent.POSITIVE)
    btn_my_today = CallbackButton(text="📋 Мои заявки (сегодня)", payload="my_requests", intent=Intent.DEFAULT)
    btn_my_month = CallbackButton(text="📅 Мои заявки за месяц", payload="my_requests_by_month", intent=Intent.DEFAULT)
    return Attachment(type="inline_keyboard", payload=ButtonsPayload(buttons=[[btn_food], [btn_my_today], [btn_my_month]]))

# ========== ГЛАВНОЕ МЕНЮ ДЛЯ АДМИНИСТРАТОРОВ ==========
def admin_menu():
    btn_food = CallbackButton(text="🍽️ Подать заявку", payload="new_food_request", intent=Intent.POSITIVE)
    btn_edit = CallbackButton(text="✏️ Редактировать заявку", payload="edit_request", intent=Intent.DEFAULT)
    btn_all_requests = CallbackButton(text="📋 Все заявки по классу", payload="all_requests_by_class", intent=Intent.DEFAULT)
    btn_report = CallbackButton(text="📊 Сформировать отчёт", payload="make_report", intent=Intent.DEFAULT)
    btn_view_requests = CallbackButton(text="📋 Кто подал заявку", payload="view_requests_by_shift", intent=Intent.DEFAULT)
    btn_my = CallbackButton(text="📋 Мои заявки", payload="my_requests", intent=Intent.DEFAULT)
    return Attachment(type="inline_keyboard", payload=ButtonsPayload(buttons=[
        [btn_food], [btn_edit], [btn_all_requests], [btn_report], [btn_view_requests], [btn_my]
    ]))

# ========== МЕНЮ ВЫБОРА ПЕРИОДА ОТЧЁТА ==========
def report_period_menu():
    buttons = [
        [CallbackButton(text="📅 Ежедневный отчёт", payload="report_daily", intent=Intent.DEFAULT)],
        [CallbackButton(text="📆 Еженедельный отчёт", payload="report_weekly", intent=Intent.DEFAULT)],
        [CallbackButton(text="📊 Ежемесячный отчёт", payload="report_monthly", intent=Intent.DEFAULT)],
        [CallbackButton(text="◀️ Назад", payload="back_to_admin_menu", intent=Intent.DEFAULT)],
        [CallbackButton(text="❌ Отмена", payload="cancel", intent=Intent.NEGATIVE)]
    ]
    return Attachment(type="inline_keyboard", payload=ButtonsPayload(buttons=buttons))

# ========== МЕНЮ ВЫБОРА СМЕНЫ ==========
def shift_menu():
    buttons = [
        [CallbackButton(text="🟢 1 смена", payload="shift_1", intent=Intent.DEFAULT)],
        [CallbackButton(text="🔵 2 смена", payload="shift_2", intent=Intent.DEFAULT)],
        [CallbackButton(text="◀️ Назад", payload="back_to_admin_menu", intent=Intent.DEFAULT)],
        [CallbackButton(text="❌ Отмена", payload="cancel", intent=Intent.NEGATIVE)]
    ]
    return Attachment(type="inline_keyboard", payload=ButtonsPayload(buttons=buttons))

# ========== МЕНЮ ВЫБОРА МЕСЯЦА ДЛЯ УЧИТЕЛЯ ==========
def month_menu_teacher():
    buttons = [
        [CallbackButton(text="📅 Январь", payload="month_1", intent=Intent.DEFAULT),
         CallbackButton(text="📅 Февраль", payload="month_2", intent=Intent.DEFAULT)],
        [CallbackButton(text="📅 Март", payload="month_3", intent=Intent.DEFAULT),
         CallbackButton(text="📅 Апрель", payload="month_4", intent=Intent.DEFAULT)],
        [CallbackButton(text="📅 Май", payload="month_5", intent=Intent.DEFAULT),
         CallbackButton(text="📅 Июнь", payload="month_6", intent=Intent.DEFAULT)],
        [CallbackButton(text="📅 Июль", payload="month_7", intent=Intent.DEFAULT),
         CallbackButton(text="📅 Август", payload="month_8", intent=Intent.DEFAULT)],
        [CallbackButton(text="📅 Сентябрь", payload="month_9", intent=Intent.DEFAULT),
         CallbackButton(text="📅 Октябрь", payload="month_10", intent=Intent.DEFAULT)],
        [CallbackButton(text="📅 Ноябрь", payload="month_11", intent=Intent.DEFAULT),
         CallbackButton(text="📅 Декабрь", payload="month_12", intent=Intent.DEFAULT)],
        [CallbackButton(text="◀️ Назад", payload="back_to_main_menu", intent=Intent.DEFAULT)],
        [CallbackButton(text="❌ Отмена", payload="cancel", intent=Intent.NEGATIVE)]
    ]
    return Attachment(type="inline_keyboard", payload=ButtonsPayload(buttons=buttons))

# ========== МЕНЮ ВЫБОРА МЕСЯЦА ДЛЯ АДМИНИСТРАТОРА ==========
def month_menu_admin():
    buttons = [
        [CallbackButton(text="📅 Январь", payload="month_1", intent=Intent.DEFAULT),
         CallbackButton(text="📅 Февраль", payload="month_2", intent=Intent.DEFAULT)],
        [CallbackButton(text="📅 Март", payload="month_3", intent=Intent.DEFAULT),
         CallbackButton(text="📅 Апрель", payload="month_4", intent=Intent.DEFAULT)],
        [CallbackButton(text="📅 Май", payload="month_5", intent=Intent.DEFAULT),
         CallbackButton(text="📅 Июнь", payload="month_6", intent=Intent.DEFAULT)],
        [CallbackButton(text="📅 Июль", payload="month_7", intent=Intent.DEFAULT),
         CallbackButton(text="📅 Август", payload="month_8", intent=Intent.DEFAULT)],
        [CallbackButton(text="📅 Сентябрь", payload="month_9", intent=Intent.DEFAULT),
         CallbackButton(text="📅 Октябрь", payload="month_10", intent=Intent.DEFAULT)],
        [CallbackButton(text="📅 Ноябрь", payload="month_11", intent=Intent.DEFAULT),
         CallbackButton(text="📅 Декабрь", payload="month_12", intent=Intent.DEFAULT)],
        [CallbackButton(text="◀️ Назад", payload="back_to_admin_menu", intent=Intent.DEFAULT)],
        [CallbackButton(text="❌ Отмена", payload="cancel", intent=Intent.NEGATIVE)]
    ]
    return Attachment(type="inline_keyboard", payload=ButtonsPayload(buttons=buttons))

# ========== МЕНЮ ВЫБОРА КЛАССА ДЛЯ ПРОСМОТРА ЗАЯВОК (АДМИН) ==========
def class_selection_menu(classes: list):
    buttons = []
    row = []
    for i, class_name in enumerate(classes):
        row.append(CallbackButton(text=class_name, payload=f"view_class_{class_name}", intent=Intent.DEFAULT))
        if len(row) == 3:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    
    buttons.append([CallbackButton(text="◀️ Назад", payload="back_to_month_selection", intent=Intent.DEFAULT)])
    buttons.append([CallbackButton(text="❌ Отмена", payload="cancel", intent=Intent.NEGATIVE)])
    
    return Attachment(type="inline_keyboard", payload=ButtonsPayload(buttons=buttons))

# ========== ВЫБОР ЗДАНИЯ (С ПРОДЛЕНКОЙ) ==========
def building_menu():
    btn1 = CallbackButton(text="🏫 ул. Марченко", payload="building_Марченко", intent=Intent.POSITIVE)
    btn2 = CallbackButton(text="🏫 ул. Танкистов", payload="building_Танкистов", intent=Intent.POSITIVE)
    btn_home = CallbackButton(text="🏠 Надомное отделение", payload="building_Надомное", intent=Intent.POSITIVE)
    btn_after = CallbackButton(text="⏰ Продленка", payload="building_Продленка", intent=Intent.POSITIVE)
    cancel = CallbackButton(text="❌ Отмена", payload="cancel", intent=Intent.NEGATIVE)
    return Attachment(type="inline_keyboard", payload=ButtonsPayload(buttons=[[btn1], [btn2], [btn_home], [btn_after], [cancel]]))

# ========== ВЫБОР СТУПЕНИ ДЛЯ ОБЫЧНЫХ ЗДАНИЙ ==========
def stage_menu():
    btns = [
        CallbackButton(text="📚 1-4 классы", payload="stage_1", intent=Intent.DEFAULT),
        CallbackButton(text="📖 5-9 классы", payload="stage_2", intent=Intent.DEFAULT),
        CallbackButton(text="🎓 10-11 классы", payload="stage_3", intent=Intent.DEFAULT),
        CallbackButton(text="◀️ Назад", payload="back_to_building", intent=Intent.DEFAULT),
        CallbackButton(text="❌ Отмена", payload="cancel", intent=Intent.NEGATIVE)
    ]
    return Attachment(type="inline_keyboard", payload=ButtonsPayload(buttons=[[btns[0]], [btns[1]], [btns[2]], [btns[3]], [btns[4]]]))

# ========== ВЫБОР СТУПЕНИ ДЛЯ НАДОМНОГО ОТДЕЛЕНИЯ ==========
def stage_menu_home():
    btns = [
        CallbackButton(text="📚 1-4 классы", payload="home_stage_1", intent=Intent.DEFAULT),
        CallbackButton(text="📖 5-9 классы", payload="home_stage_2", intent=Intent.DEFAULT),
        CallbackButton(text="🎓 10-11 классы", payload="home_stage_3", intent=Intent.DEFAULT),
        CallbackButton(text="◀️ Назад", payload="back_to_building", intent=Intent.DEFAULT),
        CallbackButton(text="❌ Отмена", payload="cancel", intent=Intent.NEGATIVE)
    ]
    return Attachment(type="inline_keyboard", payload=ButtonsPayload(buttons=[[btns[0]], [btns[1]], [btns[2]], [btns[3]], [btns[4]]]))

# ========== ВЫБОР КЛАССА ДЛЯ НАДОМНОГО (БЕЗ ЛИТЕРЫ) ==========
def home_grade_menu(stage: str):
    if stage == "1":
        grades = ["1", "2", "3", "4"]
    elif stage == "2":
        grades = ["5", "6", "7", "8", "9"]
    else:
        grades = ["10", "11"]
    
    buttons = []
    row = []
    for g in grades:
        row.append(CallbackButton(text=f"{g} класс", payload=f"home_grade_{g}", intent=Intent.DEFAULT))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    
    buttons.append([CallbackButton(text="◀️ Назад", payload="back_to_home_stage", intent=Intent.DEFAULT)])
    buttons.append([CallbackButton(text="❌ Отмена", payload="cancel", intent=Intent.NEGATIVE)])
    
    return Attachment(type="inline_keyboard", payload=ButtonsPayload(buttons=buttons))

# ========== ПРОДЛЕНКА - ВЫБОР ЗДАНИЯ ==========
def after_school_building_menu():
    buttons = [
        [CallbackButton(text="🏫 ул. Марченко", payload="after_school_Марченко", intent=Intent.DEFAULT)],
        [CallbackButton(text="🏫 ул. Танкистов", payload="after_school_Танкистов", intent=Intent.DEFAULT)],
        [CallbackButton(text="◀️ Назад", payload="back_to_building", intent=Intent.DEFAULT)],
        [CallbackButton(text="❌ Отмена", payload="cancel", intent=Intent.NEGATIVE)]
    ]
    return Attachment(type="inline_keyboard", payload=ButtonsPayload(buttons=buttons))

# ========== ВЫБОР КЛАССА (ЦИФРА) ==========
def grade_menu(stage: str):
    if stage == "1":
        grades = ["1", "2", "3", "4"]
    elif stage == "2":
        grades = ["5", "6", "7", "8", "9"]
    else:
        grades = ["10", "11"]
    
    buttons = []
    row = []
    for g in grades:
        row.append(CallbackButton(text=f"{g} класс", payload=f"grade_{g}", intent=Intent.DEFAULT))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    
    buttons.append([CallbackButton(text="◀️ Назад", payload="back_to_stage", intent=Intent.DEFAULT)])
    buttons.append([CallbackButton(text="❌ Отмена", payload="cancel", intent=Intent.NEGATIVE)])
    return Attachment(type="inline_keyboard", payload=ButtonsPayload(buttons=buttons))

# ========== ВЫБОР ЛИТЕРЫ ==========
def litera_menu(grade: str, stage: str):
    if stage == "3":
        literas = ["1", "2"]
    else:
        literas = [str(i) for i in range(1, 10)]
    
    buttons = []
    row = []
    for l in literas:
        class_name = f"{grade}.{l}"
        row.append(CallbackButton(text=class_name, payload=f"class_{grade}_{l}", intent=Intent.DEFAULT))
        if len(row) == 3:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    
    buttons.append([CallbackButton(text="◀️ Назад", payload="back_to_grade", intent=Intent.DEFAULT)])
    buttons.append([CallbackButton(text="❌ Отмена", payload="cancel", intent=Intent.NEGATIVE)])
    return Attachment(type="inline_keyboard", payload=ButtonsPayload(buttons=buttons))

# ========== ВЫБОР КАТЕГОРИИ ==========
def category_menu(stage: str):
    if stage == "1":
        categories = [
            ("📚 1-4 класс", "1-4 класс"),
            ("♿ ОВЗ и инвалиды 1-4 класс", "ОВЗ и инвалиды 1-4 класс")
        ]
    else:
        categories = [
            ("💰 Без субсидии", "Без субсидии"),
            ("👨‍👩‍👧‍👦 Малообеспеченные", "Малообеспеченные"),
            ("👶 Многодетные", "Многодетные"),
            ("⭐ Участники боевых действий", "Участники боевых действий"),
            ("🏠 Семьи в ТЖС", "Семьи в ТЖС"),
            ("🏥 С нарушениями здоровья", "С нарушениями здоровья"),
            ("🎖️ Семьи военнослужащих/СВО", "Семьи военнослужащих"),
            ("♿ ОВЗ и инвалиды 5-11", "ОВЗ и инвалиды 5-11"),
            ("⚔️ Кадетские классы", "Кадетские классы")
        ]
    
    buttons = []
    for name, payload in categories:
        buttons.append([CallbackButton(text=name, payload=f"cat_{payload}", intent=Intent.DEFAULT)])
    
    buttons.append([CallbackButton(text="✅ Завершить", payload="finish_request", intent=Intent.POSITIVE)])
    buttons.append([CallbackButton(text="❌ Отмена", payload="cancel", intent=Intent.NEGATIVE)])
    return Attachment(type="inline_keyboard", payload=ButtonsPayload(buttons=buttons))

# ========== ПОДТВЕРЖДЕНИЕ ==========
def confirm_menu():
    yes = CallbackButton(text="✅ ДА, ОТПРАВИТЬ", payload="confirm_submit", intent=Intent.POSITIVE)
    no = CallbackButton(text="❌ ОТМЕНИТЬ", payload="cancel", intent=Intent.NEGATIVE)
    edit = CallbackButton(text="✏️ Добавить ещё", payload="back_to_categories", intent=Intent.DEFAULT)
    return Attachment(type="inline_keyboard", payload=ButtonsPayload(buttons=[[yes], [edit], [no]]))

# ========== МЕНЮ ВЫБОРА КЛАССА ДЛЯ РЕДАКТИРОВАНИЯ ==========
def edit_class_menu(building: str, requests_list: list):
    buttons = []
    for req in requests_list:
        class_name = req["class_name"]
        total = req["total"]
        buttons.append([CallbackButton(text=f"📖 {class_name} ({total} чел.)", payload=f"edit_class_{class_name}", intent=Intent.DEFAULT)])
    
    buttons.append([CallbackButton(text="◀️ Назад", payload="back_to_admin_menu", intent=Intent.DEFAULT)])
    buttons.append([CallbackButton(text="❌ Отмена", payload="cancel", intent=Intent.NEGATIVE)])
    
    return Attachment(type="inline_keyboard", payload=ButtonsPayload(buttons=buttons))

# ========== МЕНЮ РЕДАКТИРОВАНИЯ КАТЕГОРИИ ==========
def edit_category_menu(categories: dict, stage: str):
    if stage == "1":
        all_categories = [
            "1-4 класс",
            "ОВЗ и инвалиды 1-4 класс"
        ]
    else:
        all_categories = [
            "Без субсидии",
            "Малообеспеченные",
            "Многодетные",
            "Участники боевых действий",
            "Семьи в ТЖС",
            "С нарушениями здоровья",
            "Семьи военнослужащих",
            "ОВЗ и инвалиды 5-11",
            "Кадетские классы"
        ]
    
    buttons = []
    for cat in all_categories:
        current_qty = categories.get(cat, 0)
        buttons.append([CallbackButton(text=f"{cat}: {current_qty} чел.", payload=f"edit_cat_{cat}", intent=Intent.DEFAULT)])
    
    buttons.append([CallbackButton(text="✅ Сохранить изменения", payload="edit_save", intent=Intent.POSITIVE)])
    buttons.append([CallbackButton(text="❌ Удалить заявку", payload="edit_delete", intent=Intent.NEGATIVE)])
    buttons.append([CallbackButton(text="◀️ Назад", payload="back_to_edit_class", intent=Intent.DEFAULT)])
    
    return Attachment(type="inline_keyboard", payload=ButtonsPayload(buttons=buttons))

# ========== МЕНЮ ВВОДА НОВОГО КОЛИЧЕСТВА ==========
def edit_quantity_menu(category: str, current_qty: int):
    buttons = []
    row = []
    for i in [1, 2, 3, 4, 5, 10, 15, 20]:
        row.append(CallbackButton(text=str(i), payload=f"edit_qty_{i}", intent=Intent.DEFAULT))
        if len(row) == 4:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([CallbackButton(text="➕ Другое", payload="edit_qty_other", intent=Intent.DEFAULT)])
    buttons.append([CallbackButton(text="0 (удалить категорию)", payload="edit_qty_0", intent=Intent.NEGATIVE)])
    buttons.append([CallbackButton(text="◀️ Назад", payload="back_to_edit_categories", intent=Intent.DEFAULT)])
    
    return Attachment(type="inline_keyboard", payload=ButtonsPayload(buttons=buttons))

STAGE_NAMES = {"1": "1-4 классы", "2": "5-9 классы", "3": "10-11 классы", "home": "Надомное отделение", "after_school": "Продленка"}

print("✅ keyboards_food.py загружен")
