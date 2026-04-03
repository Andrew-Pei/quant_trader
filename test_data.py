"""
生成模拟股票数据用于测试
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def generate_mock_data(symbol: str, start_date: str = "20230101", end_date: str = "20231231") -> pd.DataFrame:
    """
    生成模拟股票数据
    
    Args:
        symbol: 股票代码
        start_date: 开始日期
        end_date: 结束日期
    
    Returns:
        DataFrame with columns: date, open, high, low, close, volume
    """
    start = pd.to_datetime(start_date)
    end = pd.to_datetime(end_date)
    
    # 生成日期序列
    dates = pd.date_range(start=start, end=end, freq='D')
    # 只保留工作日
    dates = dates[dates.weekday < 5]
    
    # 生成模拟价格数据（随机游走）
    np.random.seed(hash(symbol) % 10000)  # 使用股票代码作为随机种子
    
    n = len(dates)
    returns = np.random.normal(0.001, 0.02, n)  # 日收益率
    prices = 100 * (1 + returns).cumprod()  # 价格
    
    # 生成OHLC数据
    opens = prices * (1 + np.random.uniform(-0.01, 0.01, n))
    highs = np.maximum(prices, opens) * (1 + np.random.uniform(0, 0.02, n))
    lows = np.minimum(prices, opens) * (1 - np.random.uniform(0, 0.02, n))
    closes = prices
    
    # 生成成交量
    volumes = np.random.uniform(1000000, 10000000, n)
    
    df = pd.DataFrame({
        'date': dates,
        'open': opens,
        'high': highs,
        'low': lows,
        'close': closes,
        'volume': volumes
    })
    
    return df

if __name__ == "__main__":
    # 为配置文件中的股票生成模拟数据
    symbols = ['000001', '600519', '000858', '601318', '000333']
    
    for symbol in symbols:
        df = generate_mock_data(symbol)
        df.to_csv(f'data/{symbol}.csv', index=False)
        print(f"已生成 {symbol} 的模拟数据，共 {len(df)} 条记录")