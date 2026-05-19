#!/usr/bin/env python3
"""
生成演示回测结果 - 用于测试可视化脚本
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

def generate_demo_backtest_results():
    """生成演示用的回测结果数据"""

    print("正在生成演示回测数据...")

    # 创建日期范围 (过去2年)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=730)

    # 生成每个月的最后一个交易日（约22-23天/月）
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    # 只保留交易日（周一到周五）
    trading_dates = dates[dates.dayofweek < 5]
    # 按月末取最后一个交易日
    monthly_dates = trading_dates[trading_dates.is_month_end]

    # 确保有足够的数据点
    if len(monthly_dates) < 24:
        # 手动创建月度日期
        monthly_dates = []
        current_date = start_date
        while current_date <= end_date:
            # 找到当月最后一个交易日
            next_month = current_date.replace(day=1) + timedelta(days=32)
            next_month = next_month.replace(day=1)
            last_day = next_month - timedelta(days=1)

            # 回溯到最后一个交易日
            while last_day.weekday() > 4:
                last_day -= timedelta(days=1)

            if last_day >= start_date:
                monthly_dates.append(last_day)

            current_date = next_month

        monthly_dates = pd.DatetimeIndex(monthly_dates).unique().sort_values()

    # 生成净值曲线 (带有回测逻辑的模拟)
    n_months = len(monthly_dates)

    # 模拟月度收益率
    # 基础年化收益率 12%，年化波动率 15%
    annual_return = 0.12
    annual_vol = 0.15
    monthly_return_mean = annual_return / 12
    monthly_return_std = annual_vol / np.sqrt(12)

    # 生成随机但有一定趋势的月度收益率
    np.random.seed(42)
    monthly_returns = np.random.normal(monthly_return_mean, monthly_return_std, n_months)

    # 添加一些趋势性（前半段上升，后半段振荡）
    for i in range(len(monthly_returns)):
        if i < n_months // 3:
            monthly_returns[i] += 0.01  # 前期加强
        elif i > 2 * n_months // 3:
            monthly_returns[i] *= 0.8  # 后期减弱

    # 计算净值
    portfolio_values = [1.0]
    for ret in monthly_returns[1:]:
        portfolio_values.append(portfolio_values[-1] * (1 + ret))

    portfolio_values = np.array(portfolio_values)

    # 创建DataFrame
    results_df = pd.DataFrame({
        'Date': monthly_dates,
        'Portfolio_Value': portfolio_values
    })

    # 保存结果
    output_file = "/home/user/claude/backtest_results.csv"
    results_df.to_csv(output_file, index=False)
    print(f"✓ 演示回测结果已保存到 {output_file}")

    # 生成筛选股票列表
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

    stocks_df = pd.DataFrame({
        'Symbol': demo_stocks,
        'Stock_Count': len(demo_stocks)
    })

    stocks_file = "/home/user/claude/screened_stocks.csv"
    stocks_df.to_csv(stocks_file, index=False)
    print(f"✓ 演示筛选股票已保存到 {stocks_file}")

    # 打印统计信息
    total_return = (portfolio_values[-1] / portfolio_values[0] - 1) * 100

    # 计算回撤
    cummax = np.maximum.accumulate(portfolio_values)
    drawdown = (portfolio_values - cummax) / cummax
    max_drawdown = np.min(drawdown) * 100

    print(f"\n演示数据统计:")
    print(f"  总收益率: {total_return:.2f}%")
    print(f"  最大回撤: {max_drawdown:.2f}%")
    print(f"  筛选股票数: {len(demo_stocks)}")
    print(f"  回测周期: {n_months} 个月 ({monthly_dates[0].strftime('%Y-%m-%d')} 至 {monthly_dates[-1].strftime('%Y-%m-%d')})")

    return results_df, stocks_df

def generate_demo_summary():
    """生成演示汇总表"""

    summary_data = {
        "指标": [
            "总收益率(%)",
            "年化收益率(%)",
            "年化波动率(%)",
            "夏普比率",
            "最大回撤(%)",
            "回测天数",
            "开始日期",
            "结束日期"
        ],
        "数值": [
            "28.45",
            "12.67",
            "14.82",
            "0.72",
            "-18.93",
            "732",
            "2022-05-19",
            "2024-05-19"
        ]
    }

    summary_df = pd.DataFrame(summary_data)
    summary_file = "/home/user/claude/backtest_summary.csv"
    summary_df.to_csv(summary_file, index=False, encoding='utf-8')

    print(f"✓ 演示汇总表已保存到 {summary_file}")

    return summary_df

if __name__ == "__main__":
    print("="*60)
    print("量化选股回测框架 - 演示数据生成")
    print("="*60)
    print()

    # 生成演示数据
    results_df, stocks_df = generate_demo_backtest_results()
    summary_df = generate_demo_summary()

    print("\n" + "="*60)
    print("演示数据生成完成！")
    print("="*60)
    print("\n接下来可以运行可视化脚本:")
    print("  python3 visualize_backtest.py")
    print("\n这将生成:")
    print("  - backtest_chart.png (完整的回测结果图表)")
    print("  - backtest_summary.csv (性能指标汇总)")
