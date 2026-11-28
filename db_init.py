import sqlite3
import os

def init_database():
    db_path = 'finance.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("正在连接并初始化数据库...")
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        amount REAL NOT NULL,
        category TEXT NOT NULL,
        merchant TEXT,
        trans_time TEXT NOT NULL,
        created_at TEXT DEFAULT (datetime('now', 'localtime'))
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS budgets (
        category TEXT PRIMARY KEY,
        month_limit REAL NOT NULL
    )
    ''')
    cursor.execute(
    "INSERT INTO transactions (amount, category, merchant, trans_time) VALUES (?, ?, ?, ?)", 
    (35.5, "餐饮", "肯德基", "2026-11-28 12:30:00")
    )
    print("✅ 插入了一条测试数据！")

    conn.commit()
    conn.close()

    print(f"✅ 数据库初始化成功！已生成文件: {os.path.abspath(db_path)}")
if __name__ == "__main__":
    init_database()