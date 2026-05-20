#!/usr/bin/env python3
"""
生成可视化HTML投研报告
包含四象限图、排序对比图、对标表等
"""

import csv
from datetime import datetime

def read_csv_data(filename='semiconductor_metrics.csv'):
    """读取CSV数据"""
    data = []
    try:
        with open(filename, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                row['PE'] = float(row['PE'])
                row['PB'] = float(row['PB'])
                row['ROE(%)'] = float(row['ROE(%)'])
                row['毛利率(%)'] = float(row['毛利率(%)'])
                data.append(row)
    except Exception as e:
        print(f"Error reading CSV: {e}")
    return data

def generate_html_report():
    """生成完整的HTML报告"""
    data = read_csv_data()

    if not data:
        print("无数据可处理")
        return

    # 计算统计数据
    pe_values = [float(d['PE']) for d in data]
    pb_values = [float(d['PB']) for d in data]
    roe_values = [float(d['ROE(%)']) for d in data]
    margin_values = [float(d['毛利率(%)']) for d in data]

    # 正确计算中位数（对于偶数个元素，取中间两个的平均值）
    def get_median(values):
        sorted_vals = sorted(values)
        n = len(sorted_vals)
        if n % 2 == 0:
            return (sorted_vals[n//2 - 1] + sorted_vals[n//2]) / 2
        else:
            return sorted_vals[n//2]

    pe_median = get_median(pe_values)
    roe_median = get_median(roe_values)
    pb_median = get_median(pb_values)
    margin_median = get_median(margin_values)

    html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>A股半导体行业投研自动化分析报告</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            padding: 20px;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            overflow: hidden;
        }}

        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px 20px;
            text-align: center;
        }}

        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}

        .header p {{
            font-size: 1.1em;
            opacity: 0.9;
        }}

        .content {{
            padding: 40px;
        }}

        .section {{
            margin-bottom: 40px;
        }}

        .section-title {{
            font-size: 1.8em;
            color: #667eea;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #667eea;
        }}

        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}

        .stat-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }}

        .stat-card h3 {{
            font-size: 0.9em;
            opacity: 0.9;
            margin-bottom: 10px;
        }}

        .stat-card .value {{
            font-size: 2em;
            font-weight: bold;
        }}

        .chart-container {{
            position: relative;
            height: 400px;
            margin-bottom: 30px;
            background: white;
            border: 1px solid #eee;
            border-radius: 8px;
            padding: 20px;
        }}

        .table-container {{
            overflow-x: auto;
            border: 1px solid #ddd;
            border-radius: 8px;
            margin-top: 20px;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.9em;
        }}

        th {{
            background: #667eea;
            color: white;
            padding: 12px;
            text-align: left;
        }}

        td {{
            padding: 12px;
            border-bottom: 1px solid #eee;
        }}

        tr:hover {{
            background: #f5f5f5;
        }}

        .quadrant-table {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-top: 20px;
        }}

        .quadrant {{
            border: 2px solid #ddd;
            border-radius: 8px;
            padding: 15px;
            background: #fafafa;
        }}

        .quadrant h4 {{
            color: #667eea;
            margin-bottom: 15px;
            font-size: 1.1em;
        }}

        .company-item {{
            padding: 10px;
            margin-bottom: 8px;
            background: white;
            border-left: 3px solid #667eea;
            border-radius: 4px;
        }}

        .company-name {{
            font-weight: bold;
            color: #333;
        }}

        .company-metrics {{
            font-size: 0.85em;
            color: #666;
            margin-top: 5px;
        }}

        .footer {{
            background: #f5f5f5;
            padding: 20px;
            text-align: center;
            color: #666;
            font-size: 0.9em;
        }}

        .badge {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.8em;
            margin: 2px;
            font-weight: bold;
        }}

        .badge-good {{
            background: #d4edda;
            color: #155724;
        }}

        .badge-warning {{
            background: #fff3cd;
            color: #856404;
        }}

        .badge-danger {{
            background: #f8d7da;
            color: #721c24;
        }}

        .recommendation {{
            background: #e7f3ff;
            border-left: 4px solid #667eea;
            padding: 15px;
            margin: 10px 0;
            border-radius: 4px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 A股半导体行业投研自动化分析</h1>
            <p>一键生成行业对标分析 | 估值评估 | 投资决策支持</p>
            <p style="font-size: 0.9em; margin-top: 10px;">分析期间：2025年1月～2026年5月 | 样本数：{len(data)}家公司</p>
        </div>

        <div class="content">
            <!-- 行业基准数据 -->
            <div class="section">
                <h2 class="section-title">📈 行业基准指标</h2>
                <div class="stats-grid">
                    <div class="stat-card">
                        <h3>PE(TTM)</h3>
                        <div class="value">{sum(pe_values)/len(pe_values):.2f}x</div>
                        <div style="font-size: 0.8em; margin-top: 5px;">中位数: {pe_median:.2f}x</div>
                    </div>
                    <div class="stat-card">
                        <h3>PB</h3>
                        <div class="value">{sum(pb_values)/len(pb_values):.2f}x</div>
                        <div style="font-size: 0.8em; margin-top: 5px;">中位数: {pb_median:.2f}x</div>
                    </div>
                    <div class="stat-card">
                        <h3>ROE</h3>
                        <div class="value">{sum(roe_values)/len(roe_values):.2f}%</div>
                        <div style="font-size: 0.8em; margin-top: 5px;">中位数: {roe_median:.2f}%</div>
                    </div>
                    <div class="stat-card">
                        <h3>毛利率</h3>
                        <div class="value">{sum(margin_values)/len(margin_values):.2f}%</div>
                        <div style="font-size: 0.8em; margin-top: 5px;">中位数: {margin_median:.2f}%</div>
                    </div>
                </div>
            </div>

            <!-- PE分布图 -->
            <div class="section">
                <h2 class="section-title">💹 PE分布（倍）</h2>
                <div class="chart-container">
                    <canvas id="peChart"></canvas>
                </div>
            </div>

            <!-- ROE分布图 -->
            <div class="section">
                <h2 class="section-title">📊 ROE分布（%）</h2>
                <div class="chart-container">
                    <canvas id="roeChart"></canvas>
                </div>
            </div>

            <!-- PE vs ROE 四象限 -->
            <div class="section">
                <h2 class="section-title">🎯 四象限分析：PE vs ROE</h2>
                <p style="color: #666; margin-bottom: 20px;">中位线：PE={pe_median:.2f}x | ROE={roe_median:.2f}%</p>
                <div class="chart-container">
                    <canvas id="quadrantChart"></canvas>
                </div>
"""

    # 生成四象限分类
    quality = []  # 低PE高ROE
    growth = []   # 高PE高ROE
    cheap = []    # 低PE低ROE
    bubble = []   # 高PE低ROE

    for d in data:
        if float(d['PE']) < pe_median and float(d['ROE(%)']) > roe_median:
            quality.append(d)
        elif float(d['PE']) >= pe_median and float(d['ROE(%)']) > roe_median:
            growth.append(d)
        elif float(d['PE']) < pe_median and float(d['ROE(%)']) <= roe_median:
            cheap.append(d)
        else:
            bubble.append(d)

    html_content += """
                <div class="quadrant-table">
                    <div class="quadrant">
                        <h4 style="color: #28a745;">✓ 优质股（低PE高ROE）</h4>
"""
    for d in quality:
        html_content += f"""
                        <div class="company-item">
                            <div class="company-name">{d['名称']} ({d['代码']})</div>
                            <div class="company-metrics">PE: {d['PE']}x | ROE: {d['ROE(%)']}% | 毛利率: {d['毛利率(%)']:.1f}%</div>
                        </div>
"""

    html_content += """
                    </div>
                    <div class="quadrant">
                        <h4 style="color: #ffc107;">⚡ 成长股（高PE高ROE）</h4>
"""
    for d in growth:
        html_content += f"""
                        <div class="company-item">
                            <div class="company-name">{d['名称']} ({d['代码']})</div>
                            <div class="company-metrics">PE: {d['PE']}x | ROE: {d['ROE(%)']}% | 毛利率: {d['毛利率(%)']:.1f}%</div>
                        </div>
"""

    html_content += """
                    </div>
                    <div class="quadrant">
                        <h4 style="color: #fd7e14;">❓ 困难股（低PE低ROE）</h4>
"""
    for d in cheap:
        html_content += f"""
                        <div class="company-item">
                            <div class="company-name">{d['名称']} ({d['代码']})</div>
                            <div class="company-metrics">PE: {d['PE']}x | ROE: {d['ROE(%)']}% | 毛利率: {d['毛利率(%)']:.1f}%</div>
                        </div>
"""

    html_content += """
                    </div>
                    <div class="quadrant">
                        <h4 style="color: #dc3545;">✗ 泡沫股（高PE低ROE）</h4>
"""
    for d in bubble:
        html_content += f"""
                        <div class="company-item">
                            <div class="company-name">{d['名称']} ({d['代码']})</div>
                            <div class="company-metrics">PE: {d['PE']}x | ROE: {d['ROE(%)']}% | 毛利率: {d['毛利率(%)']:.1f}%</div>
                        </div>
"""

    html_content += """
                    </div>
                </div>
            </div>

            <!-- 对标排名表 -->
            <div class="section">
                <h2 class="section-title">📋 对标排名表</h2>
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>排名</th>
                                <th>代码</th>
                                <th>名称</th>
                                <th>PE</th>
                                <th>PB</th>
                                <th>ROE</th>
                                <th>毛利率</th>
                                <th>总市值</th>
                            </tr>
                        </thead>
                        <tbody>
"""

    # 按PE排序显示
    sorted_data = sorted(data, key=lambda x: float(x['PE']))
    for rank, d in enumerate(sorted_data, 1):
        html_content += f"""
                            <tr>
                                <td>{rank}</td>
                                <td>{d['代码']}</td>
                                <td><strong>{d['名称']}</strong></td>
                                <td>{d['PE']}</td>
                                <td>{d['PB']}</td>
                                <td>{d['ROE(%)']}</td>
                                <td>{d['毛利率(%)']}</td>
                                <td>{d['总市值(亿)']}亿</td>
                            </tr>
"""

    html_content += """
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- 投资建议 -->
            <div class="section">
                <h2 class="section-title">💡 投资建议</h2>

                <div class="recommendation">
                    <strong>✓ 优质股（低PE高ROE）</strong><br>
                    重点关注，具有较强的盈利能力和较低的估值水平，是最佳的投资对象。
                </div>

                <div class="recommendation">
                    <strong>⚡ 成长股（高PE高ROE）</strong><br>
                    跟踪观察，短期涨幅可能较大，需关注是否存在高估风险，适合风险承受力较强的投资者。
                </div>

                <div class="recommendation">
                    <strong>❓ 困难股（低PE低ROE）</strong><br>
                    谨慎观察，需关注是否存在行业风险或公司自身问题，需进一步深度分析。
                </div>

                <div class="recommendation">
                    <strong>✗ 泡沫股（高PE低ROE）</strong><br>
                    建议回避，估值泡沫与盈利不匹配，存在较大的风险。
                </div>
            </div>

            <!-- 自动化方案说明 -->
            <div class="section">
                <h2 class="section-title">🤖 自动化方案</h2>
                <div style="background: #f0f8ff; padding: 20px; border-radius: 8px; border-left: 4px solid #667eea;">
                    <h3 style="color: #667eea; margin-bottom: 15px;">定期自动生成报告</h3>
                    <ul style="line-height: 2;">
                        <li><strong>更新频率：</strong>每月/每季度自动生成</li>
                        <li><strong>数据来源：</strong>Stocki Financial Reader API</li>
                        <li><strong>覆盖指标：</strong>PE、PB、ROE、毛利率等核心财务指标</li>
                        <li><strong>输出形式：</strong>HTML可视化报告 + CSV数据文件 + 投资建议</li>
                        <li><strong>应用场景：</strong>行业研究、组合管理、风险监控、投资决策支持</li>
                    </ul>
                </div>
            </div>
        </div>

        <div class="footer">
            <p>📊 A股半导体行业投研自动化分析报告 | 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p style="margin-top: 10px; opacity: 0.7;">此报告可通过接入Stocki API定期自动生成，支持实时数据更新</p>
        </div>
    </div>

    <script>
        // 数据准备
        const companies = {companies_json};
        const data = {data_json};

        // PE Chart
        const peCtx = document.getElementById('peChart').getContext('2d');
        new Chart(peCtx, {
            type: 'bar',
            data: {
                labels: companies,
                datasets: [{
                    label: 'PE(TTM)',
                    data: data.pe,
                    backgroundColor: '#667eea',
                    borderColor: '#667eea',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: { beginAtZero: true }
                }
            }
        });

        // ROE Chart
        const roeCtx = document.getElementById('roeChart').getContext('2d');
        new Chart(roeCtx, {
            type: 'bar',
            data: {
                labels: companies,
                datasets: [{
                    label: 'ROE(%)',
                    data: data.roe,
                    backgroundColor: '#764ba2',
                    borderColor: '#764ba2',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: { beginAtZero: true }
                }
            }
        });

        // 四象限图
        const quadrantCtx = document.getElementById('quadrantChart').getContext('2d');
        new Chart(quadrantCtx, {
            type: 'scatter',
            data: {
                datasets: [
                    {
                        label: '优质股',
                        data: data.quality,
                        backgroundColor: '#28a745',
                        pointRadius: 8
                    },
                    {
                        label: '成长股',
                        data: data.growth,
                        backgroundColor: '#ffc107',
                        pointRadius: 8
                    },
                    {
                        label: '困难股',
                        data: data.cheap,
                        backgroundColor: '#fd7e14',
                        pointRadius: 8
                    },
                    {
                        label: '泡沫股',
                        data: data.bubble,
                        backgroundColor: '#dc3545',
                        pointRadius: 8
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        title: { display: true, text: 'PE(倍)' }
                    },
                    y: {
                        title: { display: true, text: 'ROE(%)' }
                    }
                }
            }
        });
    </script>
</body>
</html>
"""

    # 准备数据用于JavaScript
    companies_json = ', '.join([f"'{d['名称']}'" for d in sorted_data])
    pe_json = ', '.join([str(float(d['PE'])) for d in sorted_data])
    roe_json = ', '.join([str(float(d['ROE(%)'])) for d in sorted_data])

    # 准备四象限数据
    quality_json = ', '.join([f"{{x: {d['PE']}, y: {d['ROE(%)']}}}" for d in quality])
    growth_json = ', '.join([f"{{x: {d['PE']}, y: {d['ROE(%)']}}}" for d in growth])
    cheap_json = ', '.join([f"{{x: {d['PE']}, y: {d['ROE(%)']}}}" for d in cheap])
    bubble_json = ', '.join([f"{{x: {d['PE']}, y: {d['ROE(%)']}}}" for d in bubble])

    # 替换占位符
    html_content = html_content.replace('{companies_json}', f"[{companies_json}]")
    html_content = html_content.replace('{data_json}', f"""{{
        pe: [{pe_json}],
        roe: [{roe_json}],
        quality: [{quality_json}],
        growth: [{growth_json}],
        cheap: [{cheap_json}],
        bubble: [{bubble_json}]
    }}""")

    # 保存HTML文件
    with open('semiconductor_report.html', 'w', encoding='utf-8') as f:
        f.write(html_content)

    print("✓ HTML可视化报告已生成: semiconductor_report.html")
    print("请用浏览器打开此文件查看完整的可视化分析报告")

if __name__ == '__main__':
    generate_html_report()
