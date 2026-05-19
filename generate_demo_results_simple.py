#!/usr/bin/env python3
"""
生成演示回测结果 - 不依赖pandas
"""

from datetime import datetime, timedelta
import csv
import math

def generate_trading_dates(start_date, end_date, monthly=True):
    """生成交易日期"""
    current = start_date
    dates = []

    while current <= end_date:
        # 跳过周末
        if current.weekday() < 5:  # 0-4 是 Mon-Fri
            dates.append(current)
        current += timedelta(days=1)

    if monthly:
        # 只返回每月最后一个交易日
        monthly_dates = []
        last_month = None
        for date in dates:
            if last_month != date.month or date == dates[-1]:
                if last_month is not None and len(monthly_dates) > 0:
                    # 添加上一个月的最后一天
                    pass
                last_month = date.month
                monthly_dates.append(date)
        return monthly_dates

    return dates

def generate_demo_backtest_results():
    """生成演示回测结果"""

    print("正在生成演示回测数据...")

    # 日期范围
    end_date = datetime.now()
    start_date = end_date - timedelta(days=730)

    # 生成月末交易日
    monthly_dates = []
    current = start_date
    while current <= end_date:
        # 找下一个月的1号
        if current.month == 12:
            next_month_first = current.replace(year=current.year+1, month=1, day=1)
        else:
            next_month_first = current.replace(month=current.month+1, day=1)

        # 回到这个月的最后一个交易日
        last_day = next_month_first - timedelta(days=1)
        while last_day.weekday() > 4:  # 如果是周末
            last_day -= timedelta(days=1)

        if last_day >= start_date and last_day <= end_date:
            monthly_dates.append(last_day)

        current = next_month_first

    # 生成净值数据
    n_months = len(monthly_dates)

    # 模拟收益率
    import random
    random.seed(42)

    portfolio_values = [1.0]

    for i in range(1, n_months):
        # 基础年化收益率 12%，月度约 1%
        monthly_return = 0.01 + random.gauss(0, 0.012)  # 0.01 mean, 0.012 std

        # 添加趋势
        if i < n_months // 3:
            monthly_return += 0.005
        elif i > 2 * n_months // 3:
            monthly_return *= 0.7

        new_value = portfolio_values[-1] * (1 + monthly_return)
        portfolio_values.append(new_value)

    # 保存回测结果
    output_file = "/home/user/claude/backtest_results.csv"
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Date', 'Portfolio_Value'])

        for date, value in zip(monthly_dates, portfolio_values):
            writer.writerow([date.strftime('%Y-%m-%d'), f"{value:.6f}"])

    print(f"✓ 演示回测结果已保存到 {output_file}")

    # 生成股票列表
    demo_stocks = [
        "600519",  # 贵州茅台
        "600036",  # 招商银行
        "601398",  # 工商银行
        "600000",  # 浦发银行
        "600016",  # 民生银行
        "601988",  # 中国银行
        "600031",  # 三一重工
        "601857",  # 中国石油
        "600585",  # 海螺水泥
        "0700.HK",  # 腾讯控股
        "0941.HK",  # 中国移动
        "9988.HK",  # 阿里巴巴
        "3690.HK",  # 美团
        "6078.HK",  # JD.com
    ]

    stocks_file = "/home/user/claude/screened_stocks.csv"
    with open(stocks_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Symbol', 'Stock_Count'])
        for stock in demo_stocks:
            writer.writerow([stock, str(len(demo_stocks))])

    print(f"✓ 演示筛选股票已保存到 {stocks_file}")

    # 计算统计信息
    total_return = (portfolio_values[-1] / portfolio_values[0] - 1) * 100

    # 计算回撤
    max_value = max(portfolio_values)
    max_drawdown = 0
    for value in portfolio_values:
        drawdown = (value - max_value) / max_value
        if drawdown < max_drawdown:
            max_drawdown = drawdown

    max_drawdown *= 100

    print(f"\n演示数据统计:")
    print(f"  总收益率: {total_return:.2f}%")
    print(f"  最大回撤: {max_drawdown:.2f}%")
    print(f"  筛选股票数: {len(demo_stocks)}")
    print(f"  回测周期: {n_months} 个月 ({monthly_dates[0].strftime('%Y-%m-%d')} 至 {monthly_dates[-1].strftime('%Y-%m-%d')})")

    return True

def generate_demo_summary():
    """生成演示汇总表"""

    summary_data = [
        ["指标", "数值"],
        ["总收益率(%)", "28.45"],
        ["年化收益率(%)", "12.67"],
        ["年化波动率(%)", "14.82"],
        ["夏普比率", "0.72"],
        ["最大回撤(%)", "-18.93"],
        ["回测天数", "732"],
        ["开始日期", "2022-05-19"],
        ["结束日期", "2024-05-19"]
    ]

    summary_file = "/home/user/claude/backtest_summary.csv"
    with open(summary_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(summary_data)

    print(f"✓ 演示汇总表已保存到 {summary_file}")
    return True

if __name__ == "__main__":
    print("="*60)
    print("量化选股回测框架 - 演示数据生成")
    print("="*60)
    print()

    generate_demo_backtest_results()
    generate_demo_summary()

    print("\n" + "="*60)
    print("演示数据生成完成！")
    print("="*60)
    print("\n已生成的文件:")
    print("  - backtest_results.csv (月度组合净值)")
    print("  - screened_stocks.csv (筛选出的股票)")
    print("  - backtest_summary.csv (性能指标汇总)")
