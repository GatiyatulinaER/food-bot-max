# config.py
import os

BOT_TOKEN = "f9LHodD0cOLb9r8Ro7Ml1JTzFapk2DTAL3KKBCg4Topzt5hyGAvEUkCw_spg9bSG5UOeWnzJmI_YtzOf9Mtu"

# ID групп для заявок (куда приходят заявки от учителей)
BUILDING_1_CHAT_ID = -74169084209831      # Группа заявок Марченко
BUILDING_2_CHAT_ID = -74169176156839      # Группа заявок Танкистов

# ID групп администраторов (каждая группа получает отчёты только по своему зданию)
ADMIN_GROUP_MARCHENKO = -74184834280103   # Группа админов Марченко
ADMIN_GROUP_TANKISTOV = -74184854792871   # Группа админов Танкистов

SUPER_ADMIN_ID = 33534631

REPORTS_DIR = "reports"

os.makedirs(REPORTS_DIR, exist_ok=True)
os.makedirs(os.path.join(REPORTS_DIR, "Марченко"), exist_ok=True)
os.makedirs(os.path.join(REPORTS_DIR, "Танкистов"), exist_ok=True)

print("✅ config.py загружен")