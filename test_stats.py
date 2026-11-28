import cpp_stats

print("开始测试 C++ 模块...")
amounts = [25.0, 18.5, 42.0, 9.9]
total = cpp_stats.calculate_sum(amounts)
print(f"测试1 - 总额: {total} (预期: 95.4)")

categories = ["餐饮", "交通", "餐饮", "购物"]
cat_amounts = [25.0, 15.0, 30.0, 100.0]
summary = cpp_stats.sum_by_category(categories, cat_amounts)
print(f"测试2 - 分类汇总: {dict(summary)}") # 转成字典方便看
print("测试完成！")