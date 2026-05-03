# clear_db.py
import sqlite3


def clear_database():
    conn = sqlite3.connect("meals.db")
    cursor = conn.cursor()

    # Проверяем количество записей до очистки
    cursor.execute("SELECT COUNT(*) FROM meals")
    count_before = cursor.fetchone()[0]
    print(f"📊 Записей в БД до очистки: {count_before}")

    if count_before > 0:
        # Очищаем таблицу
        cursor.execute("DELETE FROM meals")
        # Сбрасываем счетчик ID
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='meals'")
        conn.commit()
        print(f"✅ Удалено {count_before} записей")

    # Проверяем после очистки
    cursor.execute("SELECT COUNT(*) FROM meals")
    count_after = cursor.fetchone()[0]
    print(f"📊 Записей в БД после очистки: {count_after}")

    conn.close()


def show_last_records(limit=5):
    conn = sqlite3.connect("meals.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, date, building, class_name, category, quantity, teacher_name FROM meals ORDER BY id DESC LIMIT ?",
        (limit,))
    rows = cursor.fetchall()
    conn.close()

    if rows:
        print("\n📋 Последние записи в БД:")
        for row in rows:
            print(f"   ID:{row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]} | {row[5]} | {row[6]}")
    else:
        print("\n📭 База данных пуста")


if __name__ == "__main__":
    print("=" * 50)
    print("🗑️ ОЧИСТКА БАЗЫ ДАННЫХ")
    print("=" * 50)

    # Показываем последние записи
    show_last_records()

    print("\n⚠️ ВНИМАНИЕ! Это действие удалит ВСЕ записи из базы данных!")
    confirm = input("Введите ДА для подтверждения: ")

    if confirm == "ДА":
        clear_database()
        print("\n✅ База данных очищена!")
        show_last_records()
    else:
        print("❌ Очистка отменена")

    print("\n" + "=" * 50)