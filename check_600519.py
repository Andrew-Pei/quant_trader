import pandas as pd

# 读取数据
df = pd.read_csv('data/600519.csv')
df['date'] = pd.to_datetime(df['date'])

print('贵州茅台数据:')
print(df[['date', 'close']].head(10))
print(f'\n总共 {len(df)} 条数据')
print(f'价格范围: {df["close"].min():.2f} ~ {df["close"].max():.2f}')

# 检查数据是否有问题
print(f'\n数据完整性检查:')
print(f'是否有空值: {df.isnull().any().any()}')
print(f'价格是否全部相同: {df["close"].nunique() == 1}')

# 计算均线
df['MA5'] = df['close'].rolling(window=5).mean()
df['MA20'] = df['close'].rolling(window=20).mean()

print(f'\n均线数据:')
print(df[['date', 'close', 'MA5', 'MA20']].tail(20))

# 检查交叉
cross_up = (df['MA5'] > df['MA20']) & (df['MA5'].shift(1) <= df['MA20'].shift(1))
cross_down = (df['MA5'] < df['MA20']) & (df['MA5'].shift(1) >= df['MA20'].shift(1))

print(f'\n金叉次数: {cross_up.sum()}')
print(f'死叉次数: {cross_down.sum()}')

if cross_up.sum() > 0:
    print('\n金叉日期:')
    print(df[cross_up][['date', 'close', 'MA5', 'MA20']])