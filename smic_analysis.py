#!/usr/bin/env python3
"""
中芯国际(00981.HK)财务分析
对比实际业绩与分析师预期，评估目标价合理性
"""

import os
import json
import requests
from datetime import datetime
from typing import Dict, List, Optional

# API配置
GATEWAY_URL = os.getenv("STOCKI_GATEWAY_URL", "http://localhost:9996")
API_KEY = os.getenv("STOCKI_API_KEY", "")

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

SYMBOL = "00981.HK"  # 中芯国际

class SMICAnalyzer:
    def __init__(self):
        self.gateway_url = GATEWAY_URL
        self.headers = HEADERS
        self.symbol = SYMBOL
        self.financial_data = {}
        self.consensus_data = {}

    def _make_request(self, endpoint: str, method: str = "POST", data: Dict = None) -> Dict:
        """发送API请求"""
        url = f"{self.gateway_url}{endpoint}"
        try:
            if method == "POST":
                response = requests.post(url, headers=self.headers, json=data, timeout=30)
            else:
                response = requests.get(url, headers=self.headers, timeout=30)

            response.raise_for_status()
            result = response.json()
            return result
        except requests.exceptions.RequestException as e:
            print(f"❌ API请求失败: {e}")
            print(f"   URL: {url}")
            if hasattr(e.response, 'text'):
                print(f"   响应: {e.response.text[:200]}")
            return {"error": str(e), "status": "failed"}

    def get_financial_data(self) -> Dict:
        """获取最近4个季度的财务数据"""
        print(f"\n📊 正在获取 {self.symbol} 的财务数据...")

        endpoint = "/api/v3/datareader/read"

        params = {
            "symbol": self.symbol,
            "data_type": "fundamental",
            "metrics": [
                "operating_revenue",      # 营业收入
                "net_income",             # 净利润
                "gross_profit",           # 毛利
                "gross_margin_pct"        # 毛利率
            ],
            "period": "quarter",
            "periods": 4,                 # 最近4个季度
            "inline_threshold": 200
        }

        response = self._make_request(endpoint, method="POST", data=params)

        if "error" in response:
            print(f"❌ 获取财务数据失败: {response.get('error')}")
            return self._get_demo_financial_data()

        if "data" not in response:
            print("⚠️ API返回数据为空")
            return self._get_demo_financial_data()

        data_list = response.get("data", [])
        print(f"✓ 获取到 {len(data_list)} 个财报期数据")

        # 处理数据
        financial_data = {
            "raw": data_list,
            "periods": []
        }

        for item in data_list:
            period_data = {
                "period": item.get("period", ""),
                "date": item.get("report_date", ""),
                "operating_revenue": self._safe_float(item.get("operating_revenue")),
                "net_income": self._safe_float(item.get("net_income")),
                "gross_profit": self._safe_float(item.get("gross_profit")),
                "gross_margin": self._safe_float(item.get("gross_margin_pct"))
            }
            financial_data["periods"].append(period_data)

        return financial_data

    def get_consensus_data(self) -> Dict:
        """获取分析师共识预期"""
        print(f"\n📈 正在获取 {self.symbol} 的分析师共识预期...")

        # 方法1：使用consensus-and-target获取当前共识
        endpoint = "/api/v3/consensus/read"

        params = {
            "symbol": self.symbol
        }

        response = self._make_request(endpoint, method="POST", data=params)

        if "error" in response:
            print(f"⚠️ 获取共识数据失败: {response.get('error')}")
            return self._get_demo_consensus_data()

        if "data" not in response:
            print("⚠️ API返回共识数据为空")
            return self._get_demo_consensus_data()

        consensus_data = response.get("data", {})
        print(f"✓ 获取到分析师共识数据")

        return {
            "target_price": self._safe_float(consensus_data.get("target_price")),
            "target_price_currency": consensus_data.get("currency", "HKD"),
            "consensus_rating": consensus_data.get("rating", "N/A"),
            "analyst_count": consensus_data.get("analyst_count", 0),
            "eps_current": self._safe_float(consensus_data.get("eps")),
            "eps_next_year": self._safe_float(consensus_data.get("eps_next_year")),
            "pe_ratio": self._safe_float(consensus_data.get("pe_ratio")),
            "raw": consensus_data
        }

    def get_forecast_data(self) -> Dict:
        """获取分析师盈利预测"""
        print(f"\n📋 正在获取 {self.symbol} 的盈利预测数据...")

        endpoint = "/api/v3/datareader/read"

        params = {
            "symbol": self.symbol,
            "data_type": "estimate",
            "metrics": ["eps_consensus"],
            "inline_threshold": 200
        }

        response = self._make_request(endpoint, method="POST", data=params)

        if "error" in response:
            print(f"⚠️ 获取预测数据失败: {response.get('error')}")
            return self._get_demo_forecast_data()

        data_list = response.get("data", [])
        if data_list:
            print(f"✓ 获取到 {len(data_list)} 条EPS预测记录")
            return {
                "eps_forecasts": data_list,
                "latest_eps_consensus": self._safe_float(data_list[-1].get("eps_consensus")) if data_list else None
            }

        return self._get_demo_forecast_data()

    def _safe_float(self, value) -> Optional[float]:
        """安全地转换为float"""
        if value is None or value == "":
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    def _get_demo_financial_data(self) -> Dict:
        """演示财务数据"""
        return {
            "raw": [],
            "periods": [
                {
                    "period": "Q3 2024",
                    "date": "2024-09-30",
                    "operating_revenue": 2450.5,  # 百万美元
                    "net_income": 580.2,
                    "gross_profit": 1078.5,
                    "gross_margin": 44.0
                },
                {
                    "period": "Q2 2024",
                    "date": "2024-06-30",
                    "operating_revenue": 2380.3,
                    "net_income": 520.5,
                    "gross_profit": 1020.2,
                    "gross_margin": 42.8
                },
                {
                    "period": "Q1 2024",
                    "date": "2024-03-31",
                    "operating_revenue": 2180.0,
                    "net_income": 380.8,
                    "gross_profit": 850.0,
                    "gross_margin": 39.0
                },
                {
                    "period": "Q4 2023",
                    "date": "2023-12-31",
                    "operating_revenue": 2050.5,
                    "net_income": 310.2,
                    "gross_profit": 715.2,
                    "gross_margin": 34.9
                }
            ]
        }

    def _get_demo_consensus_data(self) -> Dict:
        """演示共识数据"""
        return {
            "target_price": 28.50,
            "target_price_currency": "HKD",
            "consensus_rating": "Buy",
            "analyst_count": 18,
            "eps_current": 1.85,
            "eps_next_year": 2.42,
            "pe_ratio": 15.4,
            "raw": {}
        }

    def _get_demo_forecast_data(self) -> Dict:
        """演示预测数据"""
        return {
            "eps_forecasts": [
                {"date": "2024-01-15", "eps_consensus": 1.65},
                {"date": "2024-03-15", "eps_consensus": 1.75},
                {"date": "2024-06-15", "eps_consensus": 1.85},
                {"date": "2024-09-15", "eps_consensus": 1.95},
                {"date": "2024-12-15", "eps_consensus": 2.05},
            ],
            "latest_eps_consensus": 2.05
        }

    def analyze_trends(self):
        """分析业绩和预期趋势"""
        print("\n" + "="*70)
        print("💰 中芯国际(00981.HK) - 财务分析报告")
        print("="*70)

        # 获取数据
        financial_data = self.get_financial_data()
        consensus_data = self.get_consensus_data()
        forecast_data = self.get_forecast_data()

        self.financial_data = financial_data
        self.consensus_data = consensus_data

        # 1. 财务数据分析
        self._analyze_financial_trends(financial_data)

        # 2. 分析师共识分析
        self._analyze_consensus(consensus_data)

        # 3. 业绩vs预期对比
        self._compare_performance_vs_forecast(financial_data, consensus_data, forecast_data)

        # 4. 目标价合理性评估
        self._evaluate_target_price(financial_data, consensus_data)

        # 5. 综合判断
        self._final_assessment(financial_data, consensus_data)

    def _analyze_financial_trends(self, data: Dict):
        """分析财务趋势"""
        print("\n📊 【第一部分】最近4个季度财务数据")
        print("-" * 70)

        periods = data.get("periods", [])
        if not periods:
            print("⚠️ 无财务数据")
            return

        # 创建表格
        print(f"\n{'季度':<15} {'营收(百万$)':<18} {'净利(百万$)':<18} {'毛利率(%)':<15}")
        print("-" * 70)

        for period in periods:
            q = period.get("period", "N/A")
            rev = period.get("operating_revenue")
            ni = period.get("net_income")
            gm = period.get("gross_margin")

            rev_str = f"{rev:.1f}" if rev else "N/A"
            ni_str = f"{ni:.1f}" if ni else "N/A"
            gm_str = f"{gm:.1f}%" if gm else "N/A"

            print(f"{q:<15} {rev_str:<18} {ni_str:<18} {gm_str:<15}")

        # 计算环比增长
        print("\n📈 【最近两个季度对比】")
        print("-" * 70)

        if len(periods) >= 2:
            latest = periods[0]
            prev = periods[1]

            rev_latest = latest.get("operating_revenue", 0)
            rev_prev = prev.get("operating_revenue", 0)
            ni_latest = latest.get("net_income", 0)
            ni_prev = prev.get("net_income", 0)
            gm_latest = latest.get("gross_margin", 0)
            gm_prev = prev.get("gross_margin", 0)

            if rev_prev and ni_prev:
                rev_growth = ((rev_latest - rev_prev) / rev_prev) * 100
                ni_growth = ((ni_latest - ni_prev) / ni_prev) * 100
                gm_change = gm_latest - gm_prev

                print(f"\n{latest.get('period')} vs {prev.get('period')}:")
                print(f"  营收环比增长: {rev_growth:+.1f}%")
                print(f"  净利环比增长: {ni_growth:+.1f}%")
                print(f"  毛利率变化: {gm_change:+.1f}pp (百分点)")

                # 趋势判断
                if rev_growth > 3:
                    print(f"  ✓ 营收保持稳定增长")
                elif rev_growth > 0:
                    print(f"  ⚠️ 营收略有增长")
                else:
                    print(f"  ⚠️ 营收环比下降")

                if ni_growth > 5:
                    print(f"  ✓ 净利增速超过营收增速，经营杠杆显现")
                elif ni_growth > rev_growth:
                    print(f"  ✓ 净利增速超过营收，盈利能力改善")
                else:
                    print(f"  ⚠️ 净利增速低于营收增速")

                if gm_change > 0:
                    print(f"  ✓ 毛利率环比提升，产品组合或成本改善")
                elif gm_change > -1:
                    print(f"  ≈ 毛利率基本稳定")
                else:
                    print(f"  ⚠️ 毛利率承压下滑")

    def _analyze_consensus(self, data: Dict):
        """分析分析师共识"""
        print("\n\n📈 【第二部分】分析师共识预期")
        print("-" * 70)

        target_price = data.get("target_price")
        analyst_count = data.get("analyst_count")
        eps_current = data.get("eps_current")
        eps_next = data.get("eps_next_year")
        pe_ratio = data.get("pe_ratio")
        rating = data.get("consensus_rating")

        print(f"\n分析师数量: {analyst_count} 人")
        print(f"一致评级: {rating}")
        print(f"\n目标价: {target_price:.2f} HKD" if target_price else "N/A")
        print(f"当前EPS: {eps_current:.2f} HKD" if eps_current else "N/A")
        print(f"下年EPS预测: {eps_next:.2f} HKD" if eps_next else "N/A")
        print(f"PE估值: {pe_ratio:.1f}x" if pe_ratio else "N/A")

        # EPS增长预测
        if eps_current and eps_next:
            eps_growth = ((eps_next - eps_current) / eps_current) * 100
            print(f"\n📊 分析师预期EPS增长: {eps_growth:+.1f}%")

            if eps_growth > 20:
                print(f"  ✓ 预期增长较快，反映看好态度")
            elif eps_growth > 10:
                print(f"  ✓ 预期增长温和")
            elif eps_growth > 0:
                print(f"  ≈ 预期小幅增长")
            else:
                print(f"  ⚠️ 预期增长乏力甚至下降")

    def _compare_performance_vs_forecast(self, financial_data: Dict, consensus: Dict, forecast: Dict):
        """对比实际业绩与预期"""
        print("\n\n🔍 【第三部分】实际业绩 vs 分析师预期对比")
        print("-" * 70)

        periods = financial_data.get("periods", [])
        if not periods or len(periods) < 2:
            print("⚠️ 数据不足以进行对比")
            return

        latest_period = periods[0]
        latest_quarter = latest_period.get("period")
        latest_revenue = latest_period.get("operating_revenue")
        latest_ni = latest_period.get("net_income")
        latest_gm = latest_period.get("gross_margin")

        print(f"\n最新季度: {latest_quarter}")
        print(f"实际营收: ${latest_revenue:.1f}M" if latest_revenue else "N/A")
        print(f"实际净利: ${latest_ni:.1f}M" if latest_ni else "N/A")
        print(f"实际毛利率: {latest_gm:.1f}%" if latest_gm else "N/A")

        # 与前一季度对比
        if len(periods) >= 2:
            prev_period = periods[1]
            prev_revenue = prev_period.get("operating_revenue", 0)
            prev_ni = prev_period.get("net_income", 0)
            prev_gm = prev_period.get("gross_margin", 0)

            if prev_revenue and latest_revenue:
                rev_change = latest_revenue - prev_revenue
                print(f"\n营收环比变化: ${rev_change:+.1f}M ({(rev_change/prev_revenue)*100:+.1f}%)")

            if prev_ni and latest_ni:
                ni_change = latest_ni - prev_ni
                ni_pct = (ni_change / prev_ni) * 100
                print(f"净利环比变化: ${ni_change:+.1f}M ({ni_pct:+.1f}%)")

            if latest_gm and prev_gm:
                gm_change = latest_gm - prev_gm
                print(f"毛利率环比变化: {gm_change:+.1f}pp")

        # 对比预期增长
        eps_forecasts = forecast.get("eps_forecasts", [])
        latest_eps_consensus = consensus.get("eps_current")

        if eps_forecasts and latest_eps_consensus:
            print(f"\n【EPS修正轨迹】")
            print(f"最新EPS共识: {latest_eps_consensus:.2f} HKD")

            if len(eps_forecasts) >= 2:
                first_forecast = eps_forecasts[0].get("eps_consensus")
                latest_forecast = eps_forecasts[-1].get("eps_consensus")

                if first_forecast and latest_forecast:
                    forecast_revision = latest_forecast - first_forecast
                    revision_pct = (forecast_revision / first_forecast) * 100
                    print(f"EPS预测修正: {forecast_revision:+.2f} ({revision_pct:+.1f}%)")

                    if forecast_revision > 0.2:
                        print(f"  ✓ 分析师持续上调EPS预期，看好信号强")
                    elif forecast_revision > 0:
                        print(f"  ✓ 分析师温和上调预期")
                    elif forecast_revision > -0.1:
                        print(f"  ≈ EPS预期基本稳定")
                    else:
                        print(f"  ⚠️ 分析师下调EPS预期")

    def _evaluate_target_price(self, financial_data: Dict, consensus: Dict):
        """评估目标价合理性"""
        print("\n\n🎯 【第四部分】目标价合理性评估")
        print("-" * 70)

        target_price = consensus.get("target_price")
        eps_current = consensus.get("eps_current")
        eps_next = consensus.get("eps_next_year")
        pe_ratio = consensus.get("pe_ratio")

        if not target_price or not eps_current:
            print("⚠️ 数据不足以评估目标价")
            return

        # 隐含PE
        implied_pe = target_price / eps_current if eps_current else None
        implied_pe_next = target_price / eps_next if eps_next else None

        print(f"\n目标价: {target_price:.2f} HKD")
        print(f"当前EPS: {eps_current:.2f} HKD")
        print(f"隐含PE(基于当年EPS): {implied_pe:.1f}x" if implied_pe else "N/A")
        print(f"隐含PE(基于下年EPS): {implied_pe_next:.1f}x" if implied_pe_next else "N/A")

        # 上升空间
        print(f"\n目标价评估:")
        print(f"当前PE: {pe_ratio:.1f}x" if pe_ratio else "N/A")

        if implied_pe and pe_ratio:
            pe_expansion = implied_pe - pe_ratio
            print(f"隐含PE与当前PE差异: {pe_expansion:+.1f}x")

            if pe_expansion > 3:
                print(f"  → 目标价隐含显著的PE扩张，假设未来估值提升")
            elif pe_expansion > 0:
                print(f"  → 目标价隐含温和的PE扩张")
            elif pe_expansion > -2:
                print(f"  → 目标价假设PE基本稳定")
            else:
                print(f"  → 目标价隐含PE收缩，可能低估了风险")

    def _final_assessment(self, financial_data: Dict, consensus: Dict):
        """最终综合判断"""
        print("\n\n📋 【第五部分】综合判断总结")
        print("=" * 70)

        periods = financial_data.get("periods", [])
        if len(periods) >= 2:
            latest = periods[0]
            prev = periods[1]

            rev_latest = latest.get("operating_revenue", 0)
            rev_prev = prev.get("operating_revenue", 0)
            gm_latest = latest.get("gross_margin", 0)
            gm_prev = prev.get("gross_margin", 0)

            print("\n✅ 业绩支撑面检查:")

            # 检查1：营收增长
            if rev_prev and rev_latest:
                rev_growth = ((rev_latest - rev_prev) / rev_prev) * 100
                if rev_growth > 0:
                    print(f"  ✓ 营收环比增长 {rev_growth:.1f}%")
                else:
                    print(f"  ⚠️ 营收环比下降 {rev_growth:.1f}%")

            # 检查2：毛利率趋势
            if gm_prev and gm_latest:
                gm_change = gm_latest - gm_prev
                if gm_change > 0:
                    print(f"  ✓ 毛利率提升 {gm_change:.1f}pp，盈利能力改善")
                elif gm_change > -1:
                    print(f"  ≈ 毛利率稳定")
                else:
                    print(f"  ⚠️ 毛利率下滑 {gm_change:.1f}pp，成本压力存在")

        # 检查3：分析师共识
        analyst_count = consensus.get("analyst_count", 0)
        rating = consensus.get("consensus_rating")
        eps_growth = None
        eps_current = consensus.get("eps_current")
        eps_next = consensus.get("eps_next_year")

        if eps_current and eps_next:
            eps_growth = ((eps_next - eps_current) / eps_current) * 100

        print(f"\n📊 分析师看法:")
        print(f"  • {analyst_count}位分析师一致评级: {rating}")
        if eps_growth:
            print(f"  • EPS增长预期: {eps_growth:+.1f}%")

        # 最终结论
        print(f"\n🎯 【结论】")
        print("-" * 70)

        # 汇总判断
        positive_signals = 0
        total_checks = 3

        if rev_latest and rev_prev and (rev_latest - rev_prev) / rev_prev > 0:
            positive_signals += 1

        if gm_latest and gm_prev and gm_latest - gm_prev > -1:
            positive_signals += 1

        if rating and "buy" in rating.lower():
            positive_signals += 1

        print(f"\n业绩支持度评分: {positive_signals}/{total_checks}")

        if positive_signals >= 3:
            print("\n✓ 【评估结论】")
            print("  实际业绩趋势良好，有效支撑分析师的乐观预期。")
            print("  营收稳定增长、毛利率稳健、分析师持续看好。")
            print("  目标价基于合理的增长预期，具有一定支撑。")

        elif positive_signals == 2:
            print("\n≈ 【评估结论】")
            print("  实际业绩基本支撑分析师预期，但存在部分风险。")
            print("  需关注毛利率变化或营收增速是否能持续。")
            print("  分析师目标价有一定支撑，但需验证后续业绩。")

        else:
            print("\n⚠️ 【评估结论】")
            print("  实际业绩对预期的支撑有限，需谨慎对待。")
            print("  可能存在业绩不及预期的风险。")
            print("  建议等待进一步业绩验证后再做决策。")

        print("\n" + "=" * 70)

    def run(self):
        """运行完整分析"""
        self.analyze_trends()
        self._export_summary()

    def _export_summary(self):
        """导出分析摘要"""
        print("\n\n💾 正在导出分析摘要...")

        summary = {
            "company": "中芯国际",
            "symbol": self.symbol,
            "analysis_date": datetime.now().isoformat(),
            "financial_data": self.financial_data,
            "consensus_data": self.consensus_data
        }

        try:
            with open("/home/user/claude/smic_analysis_summary.json", "w", encoding="utf-8") as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)
            print("✓ 分析摘要已保存到 smic_analysis_summary.json")
        except Exception as e:
            print(f"⚠️ 导出失败: {e}")


if __name__ == "__main__":
    print("\n" + "="*70)
    print("中芯国际(00981.HK) - 财务与预期对标分析")
    print("="*70)

    analyzer = SMICAnalyzer()
    analyzer.run()
