#!/usr/bin/env python3
"""
可视化回测结果 - 生成净值曲线和回撤曲线图表
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import os

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

class BacktestVisualizer:
    def __init__(self, results_file: str = "/home/user/claude/backtest_results.csv"):
        self.results_file = results_file
        self.data = None

    def load_data(self) -> bool:
        """加载回测结果数据"""
        if not os.path.exists(self.results_file):
            print(f"错误: 找不到结果文件 {self.results_file}")
            return False

        try:
            self.data = pd.read_csv(self.results_file)
            self.data['Date'] = pd.to_datetime(self.data['Date'])
            self.data = self.data.sort_values('Date')
            return True
        except Exception as e:
            print(f"加载数据失败: {e}")
            return False

    def calculate_metrics(self) -> dict:
        """计算关键指标"""
        if self.data is None or len(self.data) < 2:
            return {}

        portfolio_value = self.data['Portfolio_Value'].values

        # 总收益率
        total_return = (portfolio_value[-1] / portfolio_value[0] - 1) * 100

        # 最大回撤
        cummax = np.maximum.accumulate(portfolio_value)
        drawdown = (portfolio_value - cummax) / cummax
        max_drawdown = np.min(drawdown) * 100

        # 月度收益率
        monthly_returns = self.data.set_index('Date').resample('M')['Portfolio_Value'].last().pct_change()
        annual_return = monthly_returns.mean() * 12 * 100
        annual_vol = monthly_returns.std() * np.sqrt(12) * 100

        # 夏普比率 (假设无风险收益率为2%)
        risk_free_rate = 0.02
        sharpe_ratio = (monthly_returns.mean() * 12 - risk_free_rate) / (monthly_returns.std() * np.sqrt(12))

        return {
            "total_return": total_return,
            "max_drawdown": max_drawdown,
            "annual_return": annual_return,
            "annual_volatility": annual_vol,
            "sharpe_ratio": sharpe_ratio,
            "days": len(self.data),
            "start_date": self.data['Date'].min(),
            "end_date": self.data['Date'].max(),
        }

    def plot_results(self, output_file: str = "/home/user/claude/backtest_chart.png"):
        """生成图表"""
        if self.data is None or len(self.data) < 2:
            print("数据不足，无法生成图表")
            return False

        metrics = self.calculate_metrics()

        fig = plt.figure(figsize=(16, 10))

        # 1. 净值曲线
        ax1 = plt.subplot(2, 2, 1)
        portfolio_value = self.data['Portfolio_Value'].values
        dates = self.data['Date'].values

        ax1.plot(dates, portfolio_value, linewidth=2.5, color='#1f77b4', label='组合净值')
        ax1.fill_between(dates, 1, portfolio_value, alpha=0.2, color='#1f77b4')
        ax1.set_title('组合净值曲线', fontsize=14, fontweight='bold')
        ax1.set_xlabel('日期')
        ax1.set_ylabel('净值')
        ax1.grid(True, alpha=0.3)
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        ax1.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
        plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)
        ax1.legend()

        # 2. 回撤曲线
        ax2 = plt.subplot(2, 2, 2)
        cummax = np.maximum.accumulate(portfolio_value)
        drawdown = (portfolio_value - cummax) / cummax * 100

        ax2.fill_between(dates, drawdown, 0, alpha=0.5, color='#d62728', label='回撤')
        ax2.plot(dates, drawdown, linewidth=1.5, color='#d62728')
        ax2.set_title(f'最大回撤: {metrics.get("max_drawdown", 0):.2f}%', fontsize=14, fontweight='bold')
        ax2.set_xlabel('日期')
        ax2.set_ylabel('回撤率 (%)')
        ax2.grid(True, alpha=0.3)
        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        ax2.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
        plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)
        ax2.legend()

        # 3. 月度收益率分布
        ax3 = plt.subplot(2, 2, 3)
        monthly_data = self.data.set_index('Date').resample('M')['Portfolio_Value'].last()
        monthly_returns = monthly_data.pct_change().dropna() * 100

        colors = ['#2ca02c' if r >= 0 else '#d62728' for r in monthly_returns.values]
        ax3.bar(range(len(monthly_returns)), monthly_returns.values, color=colors, alpha=0.7)
        ax3.set_title('月度收益率分布', fontsize=14, fontweight='bold')
        ax3.set_xlabel('月份')
        ax3.set_ylabel('收益率 (%)')
        ax3.grid(True, alpha=0.3, axis='y')
        ax3.axhline(y=0, color='black', linestyle='-', linewidth=0.8)

        # 4. 性能指标表
        ax4 = plt.subplot(2, 2, 4)
        ax4.axis('off')

        metrics_text = f"""
性能指标总结

总收益率: {metrics.get('total_return', 0):.2f}%
年化收益率: {metrics.get('annual_return', 0):.2f}%
年化波动率: {metrics.get('annual_volatility', 0):.2f}%
夏普比率: {metrics.get('sharpe_ratio', 0):.2f}
最大回撤: {metrics.get('max_drawdown', 0):.2f}%

回测周期: {metrics.get('days', 0)} 交易日
开始日期: {metrics.get('start_date', '').strftime('%Y-%m-%d')}
结束日期: {metrics.get('end_date', '').strftime('%Y-%m-%d')}
        """

        ax4.text(0.1, 0.5, metrics_text, fontsize=12, verticalalignment='center',
                family='monospace', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"✓ 图表已保存到 {output_file}")
        return True

    def generate_summary_table(self, output_file: str = "/home/user/claude/backtest_summary.csv"):
        """生成汇总表格"""
        metrics = self.calculate_metrics()

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
                f"{metrics.get('total_return', 0):.2f}",
                f"{metrics.get('annual_return', 0):.2f}",
                f"{metrics.get('annual_volatility', 0):.2f}",
                f"{metrics.get('sharpe_ratio', 0):.2f}",
                f"{metrics.get('max_drawdown', 0):.2f}",
                f"{metrics.get('days', 0)}",
                f"{metrics.get('start_date', '').strftime('%Y-%m-%d')}",
                f"{metrics.get('end_date', '').strftime('%Y-%m-%d')}"
            ]
        }

        summary_df = pd.DataFrame(summary_data)
        summary_df.to_csv(output_file, index=False, encoding='utf-8')
        print(f"✓ 汇总表格已保存到 {output_file}")

        # 打印到控制台
        print("\n" + "="*50)
        print("回测性能汇总")
        print("="*50)
        for idx, row in summary_df.iterrows():
            print(f"{row['指标']:15} : {row['数值']}")
        print("="*50)

    def run(self):
        """运行可视化"""
        if not self.load_data():
            return

        print("\n正在生成回测结果图表和汇总...")

        # 生成图表
        self.plot_results()

        # 生成汇总表格
        self.generate_summary_table()

        print("\n可视化完成！")


if __name__ == "__main__":
    visualizer = BacktestVisualizer()
    visualizer.run()
