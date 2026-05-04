# run.py
import asyncio
import shutil
import os
from datetime import datetime
from bot_food_max import dp, bot

def backup_database():
    """Создаёт резервную копию базы данных"""
    if os.path.exists("meals.db"):
        backup_dir = "backups"
        os.makedirs(backup_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(backup_dir, f"meals_backup_{timestamp}.db")
        shutil.copy2("meals.db", backup_file)
        print(f"📦 Резервная копия БД создана: {backup_file}")
        
        # Удаляем старые резервные копии (старше 30 дней)
        for f in os.listdir(backup_dir):
            if f.startswith("meals_backup_"):
                file_path = os.path.join(backup_dir, f)
                if os.path.getmtime(file_path) < (datetime.now().timestamp() - 30 * 24 * 3600):
                    os.remove(file_path)
                    print(f"🗑️ Удалена старая копия: {f}")

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 БОТ-ЛАНЧБОКС ДЛЯ MAX ЗАПУЩЕН")
    print("=" * 60)
    print("📁 Отчёты: reports/Марченко/ и reports/Танкистов/")
    print("📊 Структура отчётов:")
    print("   • Марченко: 1-4 классы, 5-11 классы, Надомное отделение, Продленка")
    print("   • Танкистов: 1-4 классы, 5-9 классы, Продленка")
    print("📝 Количество учеников вводится вручную")
    print("🛡️ Защита от повторной подачи заявки на один класс в день")
    print("📧 Автоматическая отправка отчётов на email (Gmail)")
    print("👥 Просмотр заявок по сменам")
    print("✏️ Редактирование заявок администратором")
    print("📋 Просмотр всех заявок по классу за месяц (админ)")
    print("📅 Просмотр своих заявок за месяц (учитель)")
    print("📦 Автоматическое резервное копирование БД")
    print("=" * 60)
    print("✅ Бот готов к работе!")
    print("❗ Ctrl+C - остановка")
    print("=" * 60)
    
    # Создаём резервную копию при запуске
    backup_database()
    
    try:
        asyncio.run(dp.start_polling(bot))
    except KeyboardInterrupt:
        # Создаём резервную копию при остановке
        backup_database()
        print("\n🛑 Бот остановлен")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
