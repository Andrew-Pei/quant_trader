"""
Quant Trader - A股量化交易系统
"""

from .data import DataFetcher
from .strategies import (
    BaseStrategy,
    Signal,
    MACrossStrategy,
    EMACrossStrategy,
    RSIStrategy,
    get_strategy,
    STRATEGY_REGISTRY
)
from .backtest import BacktestEngine, BacktestResult
from .utils import Visualizer, print_result_summary

__version__ = '1.0.0'
__author__ = 'Andrew-Pei'

__all__ = [
    'DataFetcher',
    'BaseStrategy',
    'Signal',
    'MACrossStrategy',
    'EMACrossStrategy',
    'RSIStrategy',
    'get_strategy',
    'STRATEGY_REGISTRY',
    'BacktestEngine',
    'BacktestResult',
    'Visualizer',
    'print_result_summary'
]
