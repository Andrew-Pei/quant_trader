import pandas as pd
import sys
sys.path.insert(0, '.')

from strategies import get_strategy

# 读取数据
df = pd.read_csv('data/600519.csv')
df['date'] = pd.to_datetime(df['date'])

print('贵州茅台数据:')
print(df[['date', 'close']].head(5))
print(f'\n总共 {len(df)} 条数据')

# 初始化策略
strategy = get_strategy('ma_cross', {
    'short_window': 5,
    'long_window': 20,
    'rsi_period': 14,
    'rsi_oversold': 30,
    'rsi_overbought': 70
})

# 生成信号
signals = strategy.generate_signals(df)

print(f'\n信号统计:')
print(f'买入信号次数: {(signals["signal"] == 1).sum()}')
print(f'卖出信号次数: {(signals["signal"] == -1).sum()}')
print(f'无信号次数: {(signals["signal"] == 0).sum()}')

# 查看有信号的日期
buy_signals = signals[signals['signal'] == 1]
sell_signals = signals[signals['signal'] == -1]

if len(buy_signals) > 0:
    print(f'\n买入信号日期 ({len(buy_signals)}次):')
    print(buy_signals[['date', 'close', 'signal']])

if len(sell_signals) > 0:
    print(f'\n卖出信号日期 ({len(sell_signals)}次):')
    print(sell_signals[['date', 'close', 'signal']])

# 检查信号和价格的关系
print(f'\n信号和价格关系:')
print(f'第一个买入信号日期: {buy_signals["date"].iloc[0] if len(buy_signals) > 0 else "无"}')
print(f'第一个卖出信号日期: {sell_signals["date"].iloc[0] if len(sell_signals) > 0 else "无"}')

# 检查回测引擎逻辑
from backtest.engine import BacktestEngine

engine = BacktestEngine(
    initial_capital=100000,
    commission_rate=0.0003,
    slippage=0.001,
    position_size=0.9
)

print(f'\n回测引擎初始状态:')
print(f'初始资金: {engine.initial_capital}')
print(f'现金: {engine.cash}')
print(f'持仓: {engine.position}')