import database_manager as db
db.init_db()
print("1. 数据库初始化完毕")
import sqlite3
conn = sqlite3.connect('finance.db')
cursor = conn.cursor()
cursor.execute("INSERT INTO transactions (amount, category, merchant, trans_time) VALUES (?, ?, ?, ?)", (25.0, "餐饮", "沙县", "2026-11-21 12:00:00"))
cursor.execute("INSERT INTO transactions (amount, category, merchant, trans_time) VALUES (?, ?, ?, ?)", (10.0, "交通", "地铁", "2026-11-21 13:00:00"))
cursor.execute("INSERT OR REPLACE INTO budgets (category, month_limit) VALUES (?, ?)", ("餐饮", 50.0))
conn.commit()
conn.close()
print("2. 测试数据插入完毕")
stats = db.get_category_stats("2026-11")
print(f"3. 分类统计结果 (月份 2026-11): {stats}")
warning = db.check_budget("餐饮")
print(f"4. 餐饮预算检查结果: {warning}")
print("5. 尝试测试危险 SQL...")
try:
    db.execute_llm_sql("DROP TABLE transactions")
except Exception as e:
    print(f"   拦截成功: {e}")
res = db.execute_llm_sql("SELECT * FROM transactions WHERE category = '餐饮'")
print(f"6. 模拟大模型查询餐饮记录结果: {res}")
from database_manager import get_cpp_category_stats

print("\n--- 测试 C++ 模块结合数据库 ---")
cpp_res = get_cpp_category_stats("2026-11")
print("C++ 模块计算结果:", cpp_res)