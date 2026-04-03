"""
策略基类模块
定义所有交易策略的通用接口
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from enum import Enum
import pandas as pd


class Signal(Enum):
    """交易信号"""
    BUY = 1
    SELL = -1
    HOLD = 0


class BaseStrategy(ABC):
    """
    策略基类
    所有策略必须继承此类并实现 generate_signals 方法
    """
    
    def __init__(self, params: Optional[Dict[str, Any]] = None):
        """
        初始化策略
        
        Args:
            params: 策略参数字典
        """
        self.params = params or {}
        self.name = self.__class__.__name__
    
    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        根据数据生成交易信号
        
        Args:
            data: 包含 'date', 'open', 'high', 'low', 'close', 'volume' 的DataFrame
        
        Returns:
            添加了 'signal' 列的DataFrame，signal取值为 Signal 枚举值
        """
        pass
    
    @abstractmethod
    def get_required_data_length(self) -> int:
        """
        获取策略需要的最小数据长度
        
        Returns:
            最小数据条数
        """
        pass
    
    def validate_data(self, data: pd.DataFrame) -> bool:
        """
        验证数据格式是否正确
        
        Args:
            data: 待验证的数据
        
        Returns:
            是否有效
        """
        required_columns = ['date', 'open', 'high', 'low', 'close', 'volume']
        if not all(col in data.columns for col in required_columns):
            return False
        if len(data) < self.get_required_data_length():
            return False
        return True
    
    def set_params(self, params: Dict[str, Any]):
        """更新策略参数"""
        self.params.update(params)
    
    def get_params(self) -> Dict[str, Any]:
        """获取当前策略参数"""
        return self.params.copy()
    
    def __str__(self) -> str:
        return f"{self.name}(params={self.params})"
