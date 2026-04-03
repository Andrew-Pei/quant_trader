"""
A股数据获取模块
使用 akshare 获取股票历史数据
"""

import os
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, List

# 在导入任何网络库之前，彻底禁用代理
def _disable_all_proxies():
    """彻底禁用所有代理"""
    # 清除环境变量
    proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy',
                  'ALL_PROXY', 'all_proxy', 'SOCKS_PROXY', 'socks_proxy',
                  'NO_PROXY', 'no_proxy', 'FTP_PROXY', 'ftp_proxy']
    for var in proxy_vars:
        if var in os.environ:
            del os.environ[var]

    # Monkey patch urllib3来禁用代理
    try:
        import urllib3
        # 禁用SOCKS代理支持
        try:
            import urllib3.contrib.socks
            # 将SOCKS代理类型设为None，强制urllib3不使用SOCKS
            urllib3.contrib.socks.PROXY_TYPE_SOCKS4 = None
            urllib3.contrib.socks.PROXY_TYPE_SOCKS5 = None
        except:
            pass
    except ImportError:
        pass

_disable_all_proxies()

try:
    import baostock as bs
except ImportError:
    print("请安装 baostock: pip install baostock")
    bs = None

try:
    import akshare as ak
except ImportError:
    print("请安装 akshare: pip install akshare")
    ak = None

try:
    import requests
except ImportError:
    print("请安装 requests: pip install requests")
    requests = None


def _get_stock_data_direct(symbol: str, start_date: str, end_date: str, adjust: str = "qfq") -> pd.DataFrame:
    """直接使用requests获取股票数据，绕过代理问题"""
    if not requests:
        raise ImportError("requests 未安装")

    # 创建不使用代理的session
    session = requests.Session()
    session.trust_env = False  # 不使用系统代理
    session.proxies = {}  # 清除代理设置
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    })

    # 确定市场前缀
    market_prefix = "0" if symbol.startswith("6") else "1"

    # 构造请求URL
    url = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
    params = {
        "fields1": "f1,f2,f3,f4,f5,f6",
        "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f116",
        "ut": "7eea3edcaed734bea9cbfc24409ed989",
        "klt": "101",  # 日K线
        "fqt": "1" if adjust == "qfq" else "0",  # 前复权
        "secid": f"{market_prefix}.{symbol}",
        "beg": start_date.replace("-", ""),
        "end": end_date.replace("-", "")
    }

    try:
        response = session.get(url, params=params, timeout=15, verify=False)
        response.raise_for_status()
        data = response.json()

        if data.get("rc") != 0 or not data.get("data"):
            print(f"获取股票 {symbol} 数据失败: API返回错误")
            return pd.DataFrame()

        klines = data["data"]["klines"]
        if not klines:
            print(f"股票 {symbol} 没有数据")
            return pd.DataFrame()

        # 解析数据
        df = pd.DataFrame([line.split(",") for line in klines])
        df.columns = ['date', 'open', 'close', 'high', 'low', 'volume', 'amount',
                     'pct_change', 'change', 'turnover']

        # 转换数据类型
        df['date'] = pd.to_datetime(df['date'])
        for col in ['open', 'close', 'high', 'low', 'volume', 'amount', 'pct_change', 'change', 'turnover']:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        df = df.sort_values('date').reset_index(drop=True)

        return df[['date', 'open', 'high', 'low', 'close', 'volume']]

    except Exception as e:
        print(f"获取股票 {symbol} 数据失败: {e}")
        return pd.DataFrame()


def _get_stock_data_baostock(symbol: str, start_date: str, end_date: str, adjust: str = "qfq") -> pd.DataFrame:
    """使用baostock获取股票数据"""
    if not bs:
        raise ImportError("baostock 未安装")

    # 确定市场类型
    if symbol.startswith("6"):
        market = "sh"
        bs_symbol = f"sh.{symbol}"
    else:
        market = "sz"
        bs_symbol = f"sz.{symbol}"

    # 确定复权类型
    frequency = "d"  # 日线
    adjustflag = "2" if adjust == "qfq" else "3" if adjust == "hfq" else "1"  # 1:不复权, 2:前复权, 3:后复权

    # 转换日期格式为YYYY-MM-DD
    def format_date(date_str):
        if len(date_str) == 8:  # YYYYMMDD格式
            return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
        return date_str

    try:
        # 连接baostock
        lg = bs.login()
        if lg.error_code != '0':
            print(f"baostock登录失败: {lg.error_msg}")
            return pd.DataFrame()

        # 获取数据
        rs = bs.query_history_k_data_plus(
            bs_symbol,
            "date,open,high,low,close,volume,amount",
            start_date=format_date(start_date),
            end_date=format_date(end_date),
            frequency=frequency,
            adjustflag=adjustflag
        )

        data_list = []
        while (rs.error_code == '0') & rs.next():
            data_list.append(rs.get_row_data())

        # 断开连接
        bs.logout()

        if not data_list:
            print(f"股票 {symbol} 没有数据")
            return pd.DataFrame()

        # 转换为DataFrame
        df = pd.DataFrame(data_list, columns=['date', 'open', 'high', 'low', 'close', 'volume', 'amount'])

        # 转换数据类型
        df['date'] = pd.to_datetime(df['date'])
        for col in ['open', 'high', 'low', 'close', 'volume', 'amount']:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        df = df.sort_values('date').reset_index(drop=True)

        return df[['date', 'open', 'high', 'low', 'close', 'volume']]

    except Exception as e:
        print(f"获取股票 {symbol} 数据失败: {e}")
        return pd.DataFrame()


class DataFetcher:
    """A股数据获取器"""

    def __init__(self, cache_path: str = "./data"):
        self.cache_path = cache_path
        os.makedirs(cache_path, exist_ok=True)

    def _get_cache_path(self, symbol: str, year: str) -> str:
        """获取按年份组织的缓存路径"""
        year_dir = os.path.join(self.cache_path, year)
        os.makedirs(year_dir, exist_ok=True)
        return os.path.join(year_dir, f"{symbol}.csv")

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

        # 解析日期范围
        if start_date:
            start_dt = pd.to_datetime(start_date)
        else:
            start_dt = pd.to_datetime("20200101")

        if end_date:
            end_dt = pd.to_datetime(end_date)
        else:
            end_dt = pd.to_datetime(datetime.now().strftime("%Y%m%d"))

        # 尝试从各年份缓存读取并合并
        all_data = []
        current_year = start_dt.year
        end_year = end_dt.year

        for year in range(current_year, end_year + 1):
            cache_file = self._get_cache_path(symbol, str(year))
            if os.path.exists(cache_file):
                df = pd.read_csv(cache_file, parse_dates=['date'])
                all_data.append(df)

        if all_data:
            combined_df = pd.concat(all_data, ignore_index=True)
            combined_df = combined_df.sort_values('date').drop_duplicates(subset=['date'])

            # 过滤日期范围
            combined_df = combined_df[(combined_df['date'] >= start_dt) & (combined_df['date'] <= end_dt)]

            if not combined_df.empty:
                return combined_df
        
        # 从网络获取 - 优先使用baostock
        try:
            df = _get_stock_data_baostock(
                symbol=symbol,
                start_date=start_date or "20200101",
                end_date=end_date or datetime.now().strftime("%Y%m%d"),
                adjust=adjust
            )
            if df.empty:
                raise Exception("baostock获取数据失败，尝试其他数据源")

            # 按年份保存缓存
            for year in df['date'].dt.year.unique():
                year_data = df[df['date'].dt.year == year]
                cache_file = self._get_cache_path(symbol, str(year))
                year_data.to_csv(cache_file, index=False)

            return df[['date', 'open', 'high', 'low', 'close', 'volume']]

        except Exception as e:
            print(f"baostock获取数据失败: {e}，尝试东方财富API...")
            # 回退到东方财富API
            try:
                df = _get_stock_data_direct(
                    symbol=symbol,
                    start_date=start_date or "20200101",
                    end_date=end_date or datetime.now().strftime("%Y%m%d"),
                    adjust=adjust
                )
                if df.empty:
                    raise Exception("东方财富API获取数据失败，尝试akshare")

                # 按年份保存缓存
                for year in df['date'].dt.year.unique():
                    year_data = df[df['date'].dt.year == year]
                    cache_file = self._get_cache_path(symbol, str(year))
                    year_data.to_csv(cache_file, index=False)

                return df[['date', 'open', 'high', 'low', 'close', 'volume']]

            except Exception as e2:
                print(f"东方财富API获取数据失败: {e2}，尝试akshare...")
                # 最后回退到akshare
                if ak is None:
                    raise ImportError("akshare 未安装")

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

                except Exception as e3:
                    print(f"获取股票 {symbol} 数据失败: {e3}")
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
