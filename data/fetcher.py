"""
A股数据获取模块
使用 akshare 获取股票历史数据
"""

import os
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, List

try:
    import akshare as ak
except ImportError:
    print("请安装 akshare: pip install akshare")
    ak = None


class DataFetcher:
    """A股数据获取器"""
    
    def __init__(self, cache_path: str = "./data"):
        self.cache_path = cache_path
        os.makedirs(cache_path, exist_ok=True)
    
    def get_stock_data(
        self,
        symbol: str,
        start_date: str = None,
        end_date: str = None,
        adjust: str = "qfq"  # 前复权
    ) -> pd.DataFrame:
        """
        获取单只股票的历史数据
        
        Args:
            symbol: 股票代码，如 "000001"
            start_date: 开始日期，格式 "YYYYMMDD"
            end_date: 结束日期，格式 "YYYYMMDD"
            adjust: 复权类型 "qfq"(前复权), "hfq"(后复权), ""(不复权)
        
        Returns:
            DataFrame with columns: date, open, high, low, close, volume
        """
        if ak is None:
            raise ImportError("akshare 未安装")
        
        # 尝试从缓存读取
        cache_file = os.path.join(self.cache_path, f"{symbol}.csv")
        if os.path.exists(cache_file):
            df = pd.read_csv(cache_file, parse_dates=['date'])
            if start_date:
                start_dt = pd.to_datetime(start_date)
                df = df[df['date'] >= start_dt]
            if end_date:
                end_dt = pd.to_datetime(end_date)
                df = df[df['date'] <= end_dt]
            return df
        
        # 从网络获取
        try:
            df = ak.stock_zh_a_hist(
                symbol=symbol,
                period="daily",
                start_date=start_date or "20200101",
                end_date=end_date or datetime.now().strftime("%Y%m%d"),
                adjust=adjust
            )
            
            # 标准化列名
            df = df.rename(columns={
                '日期': 'date',
                '开盘': 'open',
                '最高': 'high',
                '最低': 'low',
                '收盘': 'close',
                '成交量': 'volume',
                '成交额': 'amount',
                '涨跌幅': 'pct_change',
                '涨跌额': 'change',
                '换手率': 'turnover'
            })
            
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date').reset_index(drop=True)
            
            # 保存缓存
            df.to_csv(cache_file, index=False)
            
            return df[['date', 'open', 'high', 'low', 'close', 'volume']]
            
        except Exception as e:
            print(f"获取股票 {symbol} 数据失败: {e}")
            return pd.DataFrame()
    
    def get_multiple_stocks(
        self,
        symbols: List[str],
        start_date: str = None,
        end_date: str = None
    ) -> dict:
        """
        批量获取多只股票数据
        
        Returns:
            dict: {symbol: DataFrame}
        """
        result = {}
        for symbol in symbols:
            print(f"正在获取 {symbol} 数据...")
            df = self.get_stock_data(symbol, start_date, end_date)
            if not df.empty:
                result[symbol] = df
            else:
                print(f"  {symbol} 获取失败，跳过")
        return result
    
    def get_realtime_quote(self, symbol: str) -> dict:
        """获取实时行情"""
        if ak is None:
            return {}
        try:
            df = ak.stock_zh_a_spot_em()
            stock = df[df['代码'] == symbol]
            if not stock.empty:
                return {
                    'symbol': symbol,
                    'name': stock['名称'].values[0],
                    'price': float(stock['最新价'].values[0]),
                    'change_pct': float(stock['涨跌幅'].values[0]),
                    'volume': float(stock['成交量'].values[0]),
                    'amount': float(stock['成交额'].values[0])
                }
        except Exception as e:
            print(f"获取实时行情失败: {e}")
        return {}
    
    def clear_cache(self):
        """清除数据缓存"""
        import shutil
        if os.path.exists(self.cache_path):
            shutil.rmtree(self.cache_path)
            os.makedirs(self.cache_path, exist_ok=True)
            print("缓存已清除")


if __name__ == "__main__":
    # 测试
    fetcher = DataFetcher()
    df = fetcher.get_stock_data("000001", "20230101", "20231231")
    print(df.head())
    print(f"\n获取到 {len(df)} 条数据")
