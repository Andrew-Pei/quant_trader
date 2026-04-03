import pandas as pd
import os

files = ['000001.csv', '000858.csv', '601318.csv', '000333.csv']

print('各股票价格统计:')
print('-' * 50)
for f in files:
    df = pd.read_csv(f'data/{f}')
    symbol = os.path.splitext(f)[0]
    print(f'{symbol}: 最高价 {df["close"].max():.2f}元, 最低价 {df["close"].min():.2f}元')

print('\n贵州茅台价格:')
df_mt = pd.read_csv('data/600519.csv')
print(f'最高价: {df_mt["close"].max():.2f}元')
print(f'最低价: {df_mt["close"].min():.2f}元')
print(f'平均价: {df_mt["close"].mean():.2f}元')

print(f'\n购买100股贵州茅台需要的资金:')
avg_price = df_mt["close"].mean()
cost_100_shares = avg_price * 100 * 1.001  # 含滑点
print(f'约 {cost_100_shares:.2f}元')

print(f'\n当前配置:')
print(f'初始资金: 100,000元')
print(f'仓位比例: 90%')
print(f'可买入金额: 90,000元')
print(f'结论: 无法购买贵州茅台（需要约{cost_100_shares:.0f}元，但只有90,000元）')