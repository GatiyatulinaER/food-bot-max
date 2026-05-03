# run.py
import asyncio
from bot_food_max import dp, bot

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 БОТ-ЛАНЧБОКС ДЛЯ MAX ЗАПУЩЕН")
    print("=" * 60)
    print("📁 Отчёты: reports/Марченко/ и reports/Танкистов/")
    print("📊 Отчёты формируются по зданию группы администраторов")
    print("📝 Количество учеников вводится вручную")
    print("🛡️ Защита от повторной подачи заявки на один класс в день")
    print("📧 Автоматическая отправка отчётов на email (Gmail)")
    print("👥 Просмотр заявок по сменам")
    print("✏️ Редактирование заявок администратором")
    print("📋 Просмотр всех заявок по классу за месяц")
    print("=" * 60)
    print("✅ Бот готов к работе!")
    print("❗ Ctrl+C - остановка")
    print("=" * 60)

    try:
        asyncio.run(dp.start_polling(bot))
    except KeyboardInterrupt:
        print("\n🛑 Бот остановлен")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")