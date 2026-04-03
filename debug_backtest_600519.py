import pandas as pd
import sys
sys.path.insert(0, '.')

from strategies import get_strategy
from backtest.engine import BacktestEngine

# 读取数据
df = pd.read_csv('data/600519.csv')
df['date'] = pd.to_datetime(df['date'])

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

# 初始化回测引擎
engine = BacktestEngine(
    initial_capital=100000,
    commission_rate=0.0003,
    slippage=0.001,
    position_size=0.9
)

print('开始回测600519...\n')

# 手动运行回测
result = engine.run(
    symbol='600519',
    data=df,
    signals=signals,
    strategy_name='ma_cross'
)

print(f'\n回测结果:')
print(f'交易次数: {result.total_trades}')
print(f'盈利次数: {result.win_trades}')
print(f'亏损次数: {result.loss_trades}')

# 检查交易记录
print(f'\n交易记录数量: {len(result.trades)}')
if len(result.trades) > 0:
    print('交易详情:')
    for i, trade in enumerate(result.trades):
        print(f'{i+1}. {trade.date}: {trade.order_type.value} {trade.shares}股 @ {trade.price:.2f}')
else:
    print('没有交易记录!')

# 检查权益曲线
print(f'\n权益曲线:')
print(result.equity_curve[['date', 'equity', 'cash', 'position_value']].head(20))

# 手动检查买入逻辑
print(f'\n手动检查买入逻辑:')
print(f'初始现金: {engine.initial_capital}')
print(f'仓位比例: {engine.position_size}')
print(f'可买入金额: {engine.initial_capital * engine.position_size}')

# 模拟第一次买入
first_buy_date = df[df['date'] == pd.Timestamp('2023-02-20')]
if len(first_buy_date) > 0:
    price = first_buy_date['close'].iloc[0]
    print(f'第一次买入信号价格: {price:.2f}')

    # 计算可买入股数
    available_cash = engine.initial_capital * engine.position_size
    execution_price = price * (1 + engine.slippage)
    shares = int(available_cash / execution_price / 100) * 100

    print(f'执行价格(含滑点): {execution_price:.2f}')
    print(f'可买入股数(以100股为单位): {shares}')

    if shares >= 100:
        amount = shares * execution_price
        commission = max(amount * engine.commission_rate, 5.0)
        total_cost = amount + commission

        print(f'买入金额: {amount:.2f}')
        print(f'手续费: {commission:.2f}')
        print(f'总成本: {total_cost:.2f}')
        print(f'剩余现金: {engine.initial_capital - total_cost:.2f}')
    else:
        print(f'资金不足，无法买入! 最少需要100股，资金仅够买{shares}股')