import os
import sys

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
if not BOT_TOKEN:
    print("❌ Ошибка: BOT_TOKEN не задан в переменных окружения")
    sys.exit(1)

BUILDING_1_CHAT_ID = int(os.environ.get("BUILDING_1_CHAT_ID", 0))
BUILDING_2_CHAT_ID = int(os.environ.get("BUILDING_2_CHAT_ID", 0))
ADMIN_GROUP_MARCHENKO = int(os.environ.get("ADMIN_GROUP_MARCHENKO", 0))
ADMIN_GROUP_TANKISTOV = int(os.environ.get("ADMIN_GROUP_TANKISTOV", 0))

SUPER_ADMIN_ID = 33534631

REPORTS_DIR = "reports"

import os as _os
_os.makedirs(REPORTS_DIR, exist_ok=True)
_os.makedirs(_os.path.join(REPORTS_DIR, "Марченко"), exist_ok=True)
_os.makedirs(_os.path.join(REPORTS_DIR, "Танкистов"), exist_ok=True)

print("✅ config.py загружен")
print(f"📊 BOT_TOKEN: {'Установлен' if BOT_TOKEN else 'НЕ УСТАНОВЛЕН!'}")
print(f"🏫 BUILDING_1_CHAT_ID: {BUILDING_1_CHAT_ID}")
print(f"🏫 BUILDING_2_CHAT_ID: {BUILDING_2_CHAT_ID}")
print(f"👥 ADMIN_GROUP_MARCHENKO: {ADMIN_GROUP_MARCHENKO}")
print(f"👥 ADMIN_GROUP_TANKISTOV: {ADMIN_GROUP_TANKISTOV}")
