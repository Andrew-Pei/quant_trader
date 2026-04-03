"""
双均线交叉策略
当短期均线上穿长期均线时买入，下穿时卖出
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict, Any
from .base import BaseStrategy, Signal


class MACrossStrategy(BaseStrategy):
    """
    双均线交叉策略
    
    买入信号: 短期均线从下方上穿长期均线 (金叉)
    卖出信号: 短期均线从上方下穿长期均线 (死叉)
    """
    
    def __init__(self, params: Optional[Dict[str, Any]] = None):
        default_params = {
            'short_window': 5,   # 短期均线周期
            'long_window': 20    # 长期均线周期
        }
        if params:
            default_params.update(params)
        super().__init__(default_params)
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        生成交易信号
        
        Args:
            data: 股票历史数据
        
        Returns:
            添加了信号列的DataFrame
        """
        if not self.validate_data(data):
            raise ValueError("数据格式不正确或数据量不足")
        
        df = data.copy()
        
        short_window = self.params['short_window']
        long_window = self.params['long_window']
        
        # 计算移动平均线
        df['ma_short'] = df['close'].rolling(window=short_window).mean()
        df['ma_long'] = df['close'].rolling(window=long_window).mean()
        
        # 初始化信号列
        df['signal'] = Signal.HOLD.value
        
        # 计算均线差值
        df['ma_diff'] = df['ma_short'] - df['ma_long']
        
        # 生成信号 (从第 long_window 天开始)
        for i in range(long_window, len(df)):
            # 金叉: 短期均线上穿长期均线
            if df['ma_diff'].iloc[i-1] <= 0 and df['ma_diff'].iloc[i] > 0:
                df.loc[df.index[i], 'signal'] = Signal.BUY.value
            # 死叉: 短期均线下穿长期均线
            elif df['ma_diff'].iloc[i-1] >= 0 and df['ma_diff'].iloc[i] < 0:
                df.loc[df.index[i], 'signal'] = Signal.SELL.value
        
        return df
    
    def get_required_data_length(self) -> int:
        """需要至少 long_window + 1 条数据"""
        return self.params['long_window'] + 1


class EMACrossStrategy(BaseStrategy):
    """
    指数移动平均线交叉策略
    
    EMA对近期价格赋予更高权重，反应更灵敏
    """
    
    def __init__(self, params: Optional[Dict[str, Any]] = None):
        default_params = {
            'short_window': 5,
            'long_window': 20
        }
        if params:
            default_params.update(params)
        super().__init__(default_params)
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        if not self.validate_data(data):
            raise ValueError("数据格式不正确或数据量不足")
        
        df = data.copy()
        
        short_window = self.params['short_window']
        long_window = self.params['long_window']
        
        # 计算指数移动平均线
        df['ema_short'] = df['close'].ewm(span=short_window, adjust=False).mean()
        df['ema_long'] = df['close'].ewm(span=long_window, adjust=False).mean()
        
        df['signal'] = Signal.HOLD.value
        df['ema_diff'] = df['ema_short'] - df['ema_long']
        
        for i in range(long_window, len(df)):
            if df['ema_diff'].iloc[i-1] <= 0 and df['ema_diff'].iloc[i] > 0:
                df.loc[df.index[i], 'signal'] = Signal.BUY.value
            elif df['ema_diff'].iloc[i-1] >= 0 and df['ema_diff'].iloc[i] < 0:
                df.loc[df.index[i], 'signal'] = Signal.SELL.value
        
        return df
    
    def get_required_data_length(self) -> int:
        return self.params['long_window'] + 1
