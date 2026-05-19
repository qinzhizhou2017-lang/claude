#!/usr/bin/env python3
"""
A股港股量化选股回测框架
筛选条件：
1. 低估值（PB处于历史30%分位以下）
2. 高动量（过去6个月RSI > 60）
3. 盈利修正向上（过去30天内有分析师上调EPS预期）
"""

import os
import sys
import json
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from collections import defaultdict

# 获取API配置
GATEWAY_URL = os.getenv("STOCKI_GATEWAY_URL", "http://localhost:9996")
API_KEY = os.getenv("STOCKI_API_KEY", "")

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

class StockQuantAnalyzer:
    def __init__(self):
        self.gateway_url = GATEWAY_URL
        self.headers = HEADERS
        self.stocks_data = {}
        self.screened_stocks = []

    def _make_request(self, endpoint: str, method: str = "GET", data: Dict = None) -> Dict:
        """发送API请求"""
        url = f"{self.gateway_url}{endpoint}"
        try:
            if method == "POST":
                response = requests.post(url, headers=self.headers, json=data, timeout=30)
            else:
                response = requests.get(url, headers=self.headers, timeout=30)

            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"API请求失败: {e}")
            print(f"URL: {url}")
            return {"error": str(e), "status": "failed"}

    def get_stock_universe(self) -> List[str]:
        """获取A股和港股的股票列表"""
        print("正在获取股票列表...")

        # 获取沪深主板和科创板股票
        endpoint = "/api/v3/market/stock_list"
        params = {"market": ["cn_sh", "cn_sz", "hk"]}

        response = self._make_request(endpoint, method="POST", data=params)

        if "error" in response:
            print(f"获取股票列表失败: {response}")
            # 返回示例股票进行演示
            return self._get_demo_stocks()

        stocks = response.get("data", [])
        symbols = [s["symbol"] for s in stocks]
        print(f"获取到 {len(symbols)} 只股票")
        return symbols[:100]  # 演示时使用前100只

    def _get_demo_stocks(self) -> List[str]:
        """演示用的股票列表"""
        return [
            "600519", "600036", "600016", "600000", "601398",  # A股
            "601988", "601857", "600031", "601988", "600585",
            "0700.HK", "0941.HK", "9988.HK", "3690.HK", "6078.HK"  # 港股
        ]

    def get_pb_percentile(self, symbol: str) -> Optional[Dict]:
        """获取PB估值和历史分位数据"""
        print(f"获取 {symbol} 的PB数据...")

        # 先尝试获取当前PB和5年分位
        endpoint = "/api/v3/financial_context/read"
        params = {
            "symbol": symbol,
            "include_percentiles": True
        }

        response = self._make_request(endpoint, method="POST", data=params)

        if "error" not in response and "data" in response:
            data = response.get("data", {})
            return {
                "symbol": symbol,
                "pb_current": data.get("pb_ttm"),
                "pb_percentile_5y": data.get("pb_percentile_5y")
            }

        return None

    def get_rsi_indicator(self, symbol: str, days: int = 180) -> Optional[Dict]:
        """获取RSI指标数据"""
        print(f"获取 {symbol} 的RSI数据...")

        endpoint = "/api/v3/datareader/read"

        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

        params = {
            "symbol": symbol,
            "data_type": "indicator",
            "metrics": ["rsi_14"],
            "start_date": start_date,
            "end_date": end_date,
            "inline_threshold": 200
        }

        response = self._make_request(endpoint, method="POST", data=params)

        if "error" not in response and "data" in response:
            data_list = response.get("data", [])
            if data_list:
                # 获取最新的RSI值
                latest = data_list[-1]
                return {
                    "symbol": symbol,
                    "rsi_latest": latest.get("rsi_14"),
                    "rsi_all": data_list
                }

        return None

    def get_eps_revisions(self, symbol: str, days: int = 30) -> Optional[Dict]:
        """获取分析师EPS预期修正数据"""
        print(f"获取 {symbol} 的EPS修正数据...")

        endpoint = "/api/v3/datareader/read"

        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

        params = {
            "symbol": symbol,
            "data_type": "estimate",
            "metrics": ["eps_consensus"],
            "start_date": start_date,
            "end_date": end_date,
            "inline_threshold": 200
        }

        response = self._make_request(endpoint, method="POST", data=params)

        if "error" not in response and "data" in response:
            data_list = response.get("data", [])
            if len(data_list) >= 2:
                # 检查是否有上调
                first = float(data_list[0].get("eps_consensus", 0))
                latest = float(data_list[-1].get("eps_consensus", 0))

                return {
                    "symbol": symbol,
                    "eps_revised_up": latest > first,
                    "eps_change": latest - first,
                    "revision_count": len(data_list)
                }

        return None

    def screen_stocks(self, symbols: List[str]) -> List[str]:
        """按条件筛选股票"""
        print("\n开始筛选股票...")
        print("筛选条件：")
        print("  1. PB处于历史30%分位以下")
        print("  2. 过去6个月RSI > 60")
        print("  3. 过去30天内有分析师上调EPS预期")
        print()

        screened = []

        for symbol in symbols:
            try:
                # 获取PB数据
                pb_data = self.get_pb_percentile(symbol)
                if not pb_data or pb_data.get("pb_percentile_5y") is None:
                    continue

                pb_percentile = pb_data.get("pb_percentile_5y", 50)

                # 条件1: PB处于历史30%分位以下
                if pb_percentile > 30:
                    continue

                # 获取RSI数据
                rsi_data = self.get_rsi_indicator(symbol)
                if not rsi_data or rsi_data.get("rsi_latest") is None:
                    continue

                rsi_latest = rsi_data.get("rsi_latest", 0)

                # 条件2: RSI > 60
                if rsi_latest <= 60:
                    continue

                # 获取EPS修正数据
                eps_data = self.get_eps_revisions(symbol)
                if not eps_data:
                    continue

                eps_revised_up = eps_data.get("eps_revised_up", False)

                # 条件3: 有分析师上调
                if not eps_revised_up:
                    continue

                # 通过所有条件
                screened.append(symbol)
                print(f"✓ {symbol} 通过筛选")
                print(f"  - PB分位: {pb_percentile:.1f}% (<=30%)")
                print(f"  - RSI(6M): {rsi_latest:.1f} (>60)")
                print(f"  - EPS修正: 向上 (+{eps_data.get('eps_change', 0):.4f})")

            except Exception as e:
                print(f"处理 {symbol} 时出错: {e}")
                continue

        self.screened_stocks = screened
        print(f"\n筛选完成，符合条件的股票数: {len(screened)}")
        return screened

    def get_price_history(self, symbols: List[str],
                         start_date: str = None,
                         end_date: str = None) -> pd.DataFrame:
        """获取历史价格数据进行回测"""
        print(f"\n获取 {len(symbols)} 只股票的历史价格数据...")

        if end_date is None:
            end_date = datetime.now().strftime("%Y-%m-%d")
        if start_date is None:
            # 默认获取过去2年的数据
            start_date = (datetime.now() - timedelta(days=730)).strftime("%Y-%m-%d")

        endpoint = "/api/v3/datareader/read"

        all_prices = {}

        for symbol in symbols:
            params = {
                "symbol": symbol,
                "data_type": "price",
                "start_date": start_date,
                "end_date": end_date,
                "inline_threshold": 500
            }

            response = self._make_request(endpoint, method="POST", data=params)

            if "error" not in response and "data" in response:
                data_list = response.get("data", [])

                # 转换为DataFrame
                prices_df = pd.DataFrame(data_list)
                if not prices_df.empty:
                    prices_df["symbol"] = symbol
                    prices_df["date"] = pd.to_datetime(prices_df.get("date", prices_df.get("trade_date")))
                    prices_df["close"] = pd.to_numeric(prices_df.get("close"), errors='coerce')
                    all_prices[symbol] = prices_df[["date", "close"]].set_index("date")

        if not all_prices:
            print("未获取到任何价格数据")
            return pd.DataFrame()

        # 合并所有股票数据
        price_df = pd.DataFrame()
        for symbol, df in all_prices.items():
            df.columns = [symbol]
            price_df = pd.concat([price_df, df], axis=1)

        price_df = price_df.sort_index()
        print(f"获取到 {len(price_df)} 个交易日数据，{len(price_df.columns)} 只股票")

        return price_df

    def backtest_strategy(self, symbols: List[str],
                         price_df: pd.DataFrame = None,
                         rebalance_freq: str = "M") -> Dict:
        """回测等权组合策略，月度调仓"""
        print(f"\n开始回测策略（{rebalance_freq}调仓）...")

        if price_df is None:
            price_df = self.get_price_history(symbols)

        if price_df.empty:
            print("无法进行回测：缺少价格数据")
            return {}

        # 只使用有数据的股票
        valid_symbols = [s for s in symbols if s in price_df.columns]
        price_df = price_df[valid_symbols]

        # 计算月度收益率
        price_df_resampled = price_df.resample("M").last()

        # 填充缺失值
        price_df_resampled = price_df_resampled.fillna(method='ffill')

        # 计算每月收益率
        returns = price_df_resampled.pct_change().dropna()

        # 等权组合
        portfolio_returns = returns.mean(axis=1)

        # 计算累积收益
        cumulative_returns = (1 + portfolio_returns).cumprod()

        # 计算性能指标
        annual_return = portfolio_returns.mean() * 12
        annual_vol = portfolio_returns.std() * np.sqrt(12)
        sharpe_ratio = annual_return / annual_vol if annual_vol > 0 else 0

        # 计算最大回撤
        cumulative_max = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - cumulative_max) / cumulative_max
        max_drawdown = drawdown.min()

        results = {
            "portfolio_values": cumulative_returns,
            "portfolio_returns": portfolio_returns,
            "annual_return": annual_return,
            "annual_volatility": annual_vol,
            "sharpe_ratio": sharpe_ratio,
            "max_drawdown": max_drawdown,
            "total_return": cumulative_returns.iloc[-1] - 1 if len(cumulative_returns) > 0 else 0,
            "start_date": cumulative_returns.index[0] if len(cumulative_returns) > 0 else None,
            "end_date": cumulative_returns.index[-1] if len(cumulative_returns) > 0 else None,
        }

        return results

    def generate_report(self, backtest_results: Dict):
        """生成报告"""
        print("\n" + "="*60)
        print("量化选股回测报告")
        print("="*60)

        print(f"\n筛选结果:")
        print(f"  符合条件的股票数: {len(self.screened_stocks)}")
        print(f"  股票列表: {', '.join(self.screened_stocks[:10])}")
        if len(self.screened_stocks) > 10:
            print(f"           ... 等 {len(self.screened_stocks) - 10} 只")

        if backtest_results:
            print(f"\n回测周期:")
            print(f"  开始日期: {backtest_results.get('start_date')}")
            print(f"  结束日期: {backtest_results.get('end_date')}")

            print(f"\n性能指标:")
            print(f"  总收益率: {backtest_results.get('total_return', 0)*100:.2f}%")
            print(f"  年化收益: {backtest_results.get('annual_return', 0)*100:.2f}%")
            print(f"  年化波动: {backtest_results.get('annual_volatility', 0)*100:.2f}%")
            print(f"  夏普比率: {backtest_results.get('sharpe_ratio', 0):.2f}")
            print(f"  最大回撤: {backtest_results.get('max_drawdown', 0)*100:.2f}%")

        print("\n" + "="*60)

    def run(self):
        """运行完整流程"""
        # 1. 获取股票列表
        symbols = self.get_stock_universe()

        if not symbols:
            print("无法获取股票列表")
            return

        # 2. 筛选股票
        screened = self.screen_stocks(symbols)

        if not screened:
            print("没有找到符合条件的股票")
            return

        # 3. 获取价格历史数据
        price_df = self.get_price_history(screened)

        # 4. 回测
        backtest_results = self.backtest_strategy(screened, price_df)

        # 5. 生成报告
        self.generate_report(backtest_results)

        # 6. 输出详细数据
        if backtest_results and "portfolio_values" in backtest_results:
            self._output_results(screened, backtest_results)

    def _output_results(self, symbols: List[str], results: Dict):
        """输出详细结果到文件"""
        print("\n正在输出详细数据...")

        # 保存组合净值数据
        portfolio_values = results.get("portfolio_values")
        if portfolio_values is not None:
            output_df = pd.DataFrame({
                "Date": portfolio_values.index,
                "Portfolio_Value": portfolio_values.values
            })
            output_df.to_csv("/home/user/claude/backtest_results.csv", index=False)
            print("✓ 净值曲线已保存到 backtest_results.csv")

        # 保存筛选结果
        if symbols:
            symbols_df = pd.DataFrame({
                "Symbol": symbols,
                "Stock_Count": len(symbols)
            })
            symbols_df.to_csv("/home/user/claude/screened_stocks.csv", index=False)
            print("✓ 筛选结果已保存到 screened_stocks.csv")


if __name__ == "__main__":
    analyzer = StockQuantAnalyzer()
    analyzer.run()
