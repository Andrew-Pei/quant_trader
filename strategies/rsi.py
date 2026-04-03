"""
RSI (相对强弱指标) 策略
RSI超卖区买入，超买区卖出
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict, Any
from .base import BaseStrategy, Signal


class RSIStrategy(BaseStrategy):
    """
    RSI策略
    
    买入信号: RSI从下方穿越超卖线 (RSI < oversold)
    卖出信号: RSI从上方穿越超买线 (RSI > overbought)
    """
    
    def __init__(self, params: Optional[Dict[str, Any]] = None):
        default_params = {
            'rsi_period': 14,      # RSI计算周期
            'oversold': 30,        # 超卖阈值
            'overbought': 70       # 超买阈值
        }
        if params:
            default_params.update(params)
        super().__init__(default_params)
    
    def _calculate_rsi(self, prices: pd.Series, period: int) -> pd.Series:
        """
        计算RSI指标
        
        RSI = 100 - 100 / (1 + RS)
        RS = 平均上涨幅度 / 平均下跌幅度
        """
        delta = prices.diff()
        
        gain = delta.where(delta > 0, 0)
        loss = (-delta).where(delta < 0, 0)
        
        # 使用指数移动平均
        avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
        avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        if not self.validate_data(data):
            raise ValueError("数据格式不正确或数据量不足")
        
        df = data.copy()
        
        period = self.params['rsi_period']
        oversold = self.params['oversold']
        overbought = self.params['overbought']
        
        # 计算RSI
        df['rsi'] = self._calculate_rsi(df['close'], period)
        
        df['signal'] = Signal.HOLD.value
        
        # 从有RSI数据的位置开始
        start_idx = period + 1
        
        for i in range(start_idx, len(df)):
            rsi_current = df['rsi'].iloc[i]
            rsi_prev = df['rsi'].iloc[i-1]
            
            # 买入: RSI从超卖区向上穿越
            if rsi_prev <= oversold and rsi_current > oversold:
                df.loc[df.index[i], 'signal'] = Signal.BUY.value
            # 卖出: RSI从超买区向下穿越
            elif rsi_prev >= overbought and rsi_current < overbought:
                df.loc[df.index[i], 'signal'] = Signal.SELL.value
        
        return df
    
    def get_required_data_length(self) -> int:
        return self.params['rsi_period'] + 2


class RSIDivergenceStrategy(BaseStrategy):
    """
    RSI背离策略
    
    底背离: 价格创新低，但RSI未创新低 -> 买入
    顶背离: 价格创新高，但RSI未创新高 -> 卖出
    """
    
    def __init__(self, params: Optional[Dict[str, Any]] = None):
        default_params = {
            'rsi_period': 14,
            'lookback': 5,  # 回溯周期
            'oversold': 30,
            'overbought': 70
        }
        if params:
            default_params.update(params)
        super().__init__(default_params)
    
    def _calculate_rsi(self, prices: pd.Series, period: int) -> pd.Series:
        delta = prices.diff()
        gain = delta.where(delta > 0, 0)
        loss = (-delta).where(delta < 0, 0)
        avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
        avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        if not self.validate_data(data):
            raise ValueError("数据格式不正确或数据量不足")
        
        df = data.copy()
        period = self.params['rsi_period']
        lookback = self.params['lookback']
        
        df['rsi'] = self._calculate_rsi(df['close'], period)
        df['signal'] = Signal.HOLD.value
        
        start_idx = period + lookback + 1
        
        for i in range(start_idx, len(df)):
            # 检查底背离
            price_low_current = df['low'].iloc[i-lookback:i+1].min()
            price_low_prev = df['low'].iloc[i-2*lookback:i-lookback+1].min()
            
            rsi_current = df['rsi'].iloc[i]
            rsi_at_low = df['rsi'].iloc[df['low'].iloc[i-lookback:i+1].idxmin() - df.index[0]]
            
            # 底背离: 价格创新低，RSI未创新低
            if (price_low_current < price_low_prev and 
                rsi_at_low > df['rsi'].iloc[i-2*lookback:i-lookback+1].min() and
                rsi_current < self.params['oversold']):
                df.loc[df.index[i], 'signal'] = Signal.BUY.value
            
            # 检查顶背离
            price_high_current = df['high'].iloc[i-lookback:i+1].max()
            price_high_prev = df['high'].iloc[i-2*lookback:i-lookback+1].max()
            rsi_at_high = df['rsi'].iloc[df['high'].iloc[i-lookback:i+1].idxmax() - df.index[0]]
            
            if (price_high_current > price_high_prev and 
                rsi_at_high < df['rsi'].iloc[i-2*lookback:i-lookback+1].max() and
                rsi_current > self.params['overbought']):
                df.loc[df.index[i], 'signal'] = Signal.SELL.value
        
        return df
    
    def get_required_data_length(self) -> int:
        return self.params['rsi_period'] + 2 * self.params['lookback'] + 2
