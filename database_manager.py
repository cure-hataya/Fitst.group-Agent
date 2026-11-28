import sqlite3
import os

DB_PATH = 'finance.db'

def init_db():
    """1. 数据库连接与建表（初始化用）"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
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
    conn.commit()
    conn.close()

def execute_llm_sql(sql_query, params=None):
    """2. 安全执行 NL2SQL（你的守门员职责，给队友 A 用）"""

    if not sql_query.strip().upper().startswith("SELECT"):
        raise ValueError("安全拦截：只允许执行 SELECT 查询")
    forbidden = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE"]
    if any(word in sql_query.upper() for word in forbidden):
        raise ValueError("安全拦截：包含危险操作")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        if params:
            cursor.execute(sql_query, params)
        else:
            cursor.execute(sql_query)
        return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"❌ SQL执行失败: {e}")
        return None # 返回 None 代表查询失败，让 A 重试
    finally:
        conn.close()

def get_category_stats(month_str):
    """3. 消费分类统计（给前端 C 画图用）"""
    conn = sqlite3.connect(DB_PATH)
    sql = """
        SELECT category, SUM(amount) as total 
        FROM transactions 
        WHERE strftime('%Y-%m', trans_time) = ? 
        GROUP BY category
    """
    cursor = conn.execute(sql, (month_str,))
    results = cursor.fetchall()
    conn.close()
    return results

def check_budget(category):
    """4. 预算超支预警（用于记账后触发）"""
    conn = sqlite3.connect(DB_PATH)
    used = conn.execute("""
        SELECT SUM(amount) FROM transactions 
        WHERE category = ? AND strftime('%Y-%m', trans_time) = strftime('%Y-%m', 'now')
    """, (category,)).fetchone()[0] or 0
    limit = conn.execute("SELECT month_limit FROM budgets WHERE category = ?", (category,)).fetchone()
    
    conn.close()
    
    if limit and used > limit[0]:
        return f"【超支预警】{category}本月已用{used:.2f}元，超出预算{limit[0]:.2f}元！"
    return None
import cpp_stats 

def get_cpp_category_stats(month: str):
    data = get_category_stats(month) 
    categories = [row[0] for row in data]
    amounts = [row[1] for row in data]
    result = cpp_stats.sum_by_category(categories, amounts)
    return result