"""
可视化工具模块
生成策略分析图表
"""

import os
import pandas as pd
import numpy as np
from typing import Optional, List
from datetime import datetime

try:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    from matplotlib.ticker import FuncFormatter
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

from backtest.engine import BacktestResult


class Visualizer:
    """可视化工具"""

    def __init__(self, style: str = 'seaborn-v0_8-whitegrid'):
        if not HAS_MATPLOTLIB:
            raise ImportError("请安装 matplotlib: pip install matplotlib")

        # 设置中文字体 - 优先使用Windows常见字体
        import platform
        if platform.system() == 'Windows':
            # Windows系统中文字体
            plt.rcParams['font.sans-serif'] = [
                'Microsoft YaHei', 'SimHei', 'KaiTi', 'FangSong',
                'STSong', 'STKaiti', 'STFangsong', 'Arial Unicode MS'
            ]
        else:
            # 其他系统中文字体
            plt.rcParams['font.sans-serif'] = [
                'SimHei', 'Microsoft YaHei', 'WenQuanYi Micro Hei',
                'WenQuanYi Zen Hei', 'Droid Sans Fallback'
            ]

        plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

        # 设置样式
        try:
            plt.style.use(style)
        except:
            plt.style.use('seaborn-v0_8-whitegrid')
    
    def plot_equity_curve(
        self,
        result: BacktestResult,
        save_path: Optional[str] = None,
        show: bool = True
    ):
        """
        绘制权益曲线
        
        Args:
            result: 回测结果
            save_path: 保存路径
            show: 是否显示
        """
        fig, axes = plt.subplots(2, 1, figsize=(14, 10))
        
        df = result.equity_curve.copy()
        df['date'] = pd.to_datetime(df['date'])
        
        # 权益曲线
        ax1 = axes[0]
        ax1.plot(df['date'], df['equity'], label='总权益', linewidth=2, color='#2E86AB')
        ax1.axhline(y=result.initial_capital, color='gray', linestyle='--', alpha=0.5, label='初始资金')
        ax1.fill_between(df['date'], result.initial_capital, df['equity'], 
                         where=df['equity'] >= result.initial_capital, 
                         alpha=0.3, color='green', label='盈利区')
        ax1.fill_between(df['date'], result.initial_capital, df['equity'], 
                         where=df['equity'] < result.initial_capital, 
                         alpha=0.3, color='red', label='亏损区')
        
        ax1.set_title(f'{result.symbol} - {result.strategy_name} 策略权益曲线', fontsize=14)
        ax1.set_xlabel('日期')
        ax1.set_ylabel('权益 (元)')
        ax1.legend(loc='upper left')
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        ax1.yaxis.set_major_formatter(FuncFormatter(lambda x, p: f'{x/10000:.2f}万'))
        ax1.grid(True, alpha=0.3)
        
        # 回撤曲线
        ax2 = axes[1]
        equity = df['equity'].values
        rolling_max = np.maximum.accumulate(equity)
        drawdown = (equity - rolling_max) / rolling_max * 100
        
        ax2.fill_between(df['date'], 0, drawdown, color='#E74C3C', alpha=0.7)
        ax2.plot(df['date'], drawdown, color='#C0392B', linewidth=1)
        ax2.axhline(y=result.max_drawdown * 100, color='darkred', linestyle='--', 
                   label=f'最大回撤: {result.max_drawdown*100:.2f}%')
        
        ax2.set_title('回撤曲线', fontsize=14)
        ax2.set_xlabel('日期')
        ax2.set_ylabel('回撤 (%)')
        ax2.legend(loc='lower left')
        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
        
        if show:
            plt.show()
        else:
            plt.close()
        
        return fig
    
    def plot_trades(
        self,
        result: BacktestResult,
        price_data: pd.DataFrame,
        save_path: Optional[str] = None,
        show: bool = True
    ):
        """
        绘制交易信号图
        
        Args:
            result: 回测结果
            price_data: 价格数据
            save_path: 保存路径
            show: 是否显示
        """
        fig, ax = plt.subplots(figsize=(14, 8))
        
        df = price_data.copy()
        df['date'] = pd.to_datetime(df['date'])
        
        # 绘制价格线
        ax.plot(df['date'], df['close'], label='收盘价', linewidth=1.5, color='#34495E', alpha=0.8)
        
        # 标记买入点
        buy_trades = [t for t in result.trades if t.order_type.value == 'buy']
        buy_dates = [t.date for t in buy_trades]
        buy_prices = [t.price for t in buy_trades]
        
        ax.scatter(buy_dates, buy_prices, marker='^', s=100, color='#27AE60', 
                  label=f'买入 ({len(buy_trades)}次)', zorder=5)
        
        # 标记卖出点
        sell_trades = [t for t in result.trades if t.order_type.value == 'sell']
        sell_dates = [t.date for t in sell_trades]
        sell_prices = [t.price for t in sell_trades]
        
        ax.scatter(sell_dates, sell_prices, marker='v', s=100, color='#E74C3C', 
                  label=f'卖出 ({len(sell_trades)}次)', zorder=5)
        
        ax.set_title(f'{result.symbol} 交易信号图', fontsize=14)
        ax.set_xlabel('日期')
        ax.set_ylabel('价格 (元)')
        ax.legend(loc='upper left')
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
        
        if show:
            plt.show()
        else:
            plt.close()
        
        return fig
    
    def plot_performance_summary(
        self,
        result: BacktestResult,
        save_path: Optional[str] = None,
        show: bool = True
    ):
        """
        绘制业绩摘要图
        """
        fig, axes = plt.subplots(1, 2, figsize=(12, 5))
        
        # 收益率饼图
        ax1 = axes[0]
        colors = ['#27AE60', '#E74C3C']
        if result.total_return >= 0:
            sizes = [result.total_return * 100, 0]
            labels = [f'盈利\n{result.total_return*100:.2f}%', '']
            colors = ['#27AE60', 'white']
        else:
            sizes = [abs(result.total_return) * 100, 0]
            labels = [f'亏损\n{abs(result.total_return)*100:.2f}%', '']
            colors = ['#E74C3C', 'white']
        
        ax1.pie(sizes, labels=labels if sizes[0] > 0 else ['无收益'], 
               colors=colors[:1], autopct='', startangle=90)
        ax1.set_title('总收益率', fontsize=12)
        
        # 交易胜率柱状图
        ax2 = axes[1]
        trade_data = {
            '盈利': result.win_trades,
            '亏损': result.loss_trades
        }
        bars = ax2.bar(trade_data.keys(), trade_data.values(), color=['#27AE60', '#E74C3C'])
        ax2.set_title(f'交易统计 (胜率: {result.win_rate*100:.1f}%)', fontsize=12)
        ax2.set_ylabel('交易次数')
        
        for bar in bars:
            height = bar.get_height()
            ax2.annotate(f'{int(height)}',
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        ha='center', va='bottom')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
        
        if show:
            plt.show()
        else:
            plt.close()
        
        return fig
    
    def compare_strategies(
        self,
        results: List[BacktestResult],
        save_path: Optional[str] = None,
        show: bool = True
    ):
        """
        比较多个策略的权益曲线
        """
        fig, ax = plt.subplots(figsize=(14, 8))
        
        colors = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#3B1F2B']
        
        for i, result in enumerate(results):
            df = result.equity_curve.copy()
            df['date'] = pd.to_datetime(df['date'])
            
            # 标准化到初始资金
            normalized = df['equity'] / result.initial_capital * 100
            ax.plot(df['date'], normalized, 
                   label=f'{result.strategy_name} (年化{result.annual_return*100:.1f}%)',
                   linewidth=2, color=colors[i % len(colors)])
        
        ax.axhline(y=100, color='gray', linestyle='--', alpha=0.5, label='基准')
        ax.set_title('策略比较 - 权益曲线', fontsize=14)
        ax.set_xlabel('日期')
        ax.set_ylabel('权益指数 (初始=100)')
        ax.legend(loc='upper left')
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
        
        if show:
            plt.show()
        else:
            plt.close()
        
        return fig


def print_result_summary(result: BacktestResult):
    """打印回测结果摘要"""
    print("\n" + "=" * 60)
    print(f"回测结果摘要 - {result.symbol}")
    print("=" * 60)
    print(f"策略名称: {result.strategy_name}")
    print(f"回测区间: {result.start_date.strftime('%Y-%m-%d')} ~ {result.end_date.strftime('%Y-%m-%d')}")
    print("-" * 60)
    print("【收益指标】")
    print(f"  初始资金: {result.initial_capital:,.2f} 元")
    print(f"  最终资金: {result.final_capital:,.2f} 元")
    print(f"  总收益率: {result.total_return*100:+.2f}%")
    print(f"  年化收益: {result.annual_return*100:+.2f}%")
    print("-" * 60)
    print("【风险指标】")
    print(f"  最大回撤: {result.max_drawdown*100:.2f}%")
    print(f"  收益波动: {result.volatility*100:.2f}%")
    print(f"  夏普比率: {result.sharpe_ratio:.2f}")
    print("-" * 60)
    print("【交易统计】")
    print(f"  总交易数: {result.total_trades} 次")
    print(f"  盈利次数: {result.win_trades} 次")
    print(f"  亏损次数: {result.loss_trades} 次")
    print(f"  胜率: {result.win_rate*100:.1f}%")
    print(f"  盈亏比: {result.profit_factor:.2f}")
    print("=" * 60 + "\n")
