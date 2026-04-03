from .base import BaseStrategy, Signal
from .ma_cross import MACrossStrategy, EMACrossStrategy
from .rsi import RSIStrategy, RSIDivergenceStrategy


# 策略注册表
STRATEGY_REGISTRY = {
    'ma_cross': MACrossStrategy,
    'ema_cross': EMACrossStrategy,
    'rsi': RSIStrategy,
    'rsi_divergence': RSIDivergenceStrategy
}


def get_strategy(name: str, params: dict = None):
    """
    根据名称获取策略实例
    
    Args:
        name: 策略名称
        params: 策略参数
    
    Returns:
        策略实例
    """
    if name not in STRATEGY_REGISTRY:
        raise ValueError(f"未知的策略: {name}. 可用策略: {list(STRATEGY_REGISTRY.keys())}")
    return STRATEGY_REGISTRY[name](params)


__all__ = [
    'BaseStrategy',
    'Signal',
    'MACrossStrategy',
    'EMACrossStrategy',
    'RSIStrategy',
    'RSIDivergenceStrategy',
    'get_strategy',
    'STRATEGY_REGISTRY'
]
