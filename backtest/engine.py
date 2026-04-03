"""
回测引擎
模拟历史交易，评估策略表现
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class OrderType(Enum):
    BUY = "buy"
    SELL = "sell"


@dataclass
class Trade:
    """交易记录"""
    date: datetime
    symbol: str
    order_type: OrderType
    price: float
    shares: int
    amount: float
    commission: float
    pnl: float = 0.0  # 仅卖出时有值


@dataclass
class Position:
    """持仓信息"""
    symbol: str
    shares: int
    avg_cost: float
    current_price: float
    market_value: float
    pnl: float
    pnl_pct: float


@dataclass
class BacktestResult:
    """回测结果"""
    # 基本信息
    symbol: str
    strategy_name: str
    start_date: datetime
    end_date: datetime
    
    # 收益指标
    initial_capital: float
    final_capital: float
    total_return: float  # 总收益率
    annual_return: float  # 年化收益率
    
    # 风险指标
    max_drawdown: float  # 最大回撤
    max_drawdown_duration: int  # 最大回撤持续天数
    volatility: float  # 收益波动率
    sharpe_ratio: float  # 夏普比率
    
    # 交易统计
    total_trades: int  # 总交易次数
    win_trades: int  # 盈利次数
    loss_trades: int  # 亏损次数
    win_rate: float  # 胜率
    profit_factor: float  # 盈亏比
    
    # 详细数据
    trades: List[Trade] = field(default_factory=list)
    equity_curve: pd.DataFrame = None
    positions_history: List[Dict] = field(default_factory=list)


class BacktestEngine:
    """
    回测引擎
    
    功能:
    1. 模拟历史交易
    2. 计算收益指标
    3. 评估策略风险
    """
    
    def __init__(
        self,
        initial_capital: float = 100000,
        commission_rate: float = 0.0003,
        slippage: float = 0.001,
        position_size: float = 0.9
    ):
        """
        初始化回测引擎
        
        Args:
            initial_capital: 初始资金
            commission_rate: 手续费率 (默认万分之三)
            slippage: 滑点 (默认0.1%)
            position_size: 仓位比例 (默认90%)
        """
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate
        self.slippage = slippage
        self.position_size = position_size
        
        # 运行时状态
        self.cash = initial_capital
        self.position: Optional[Position] = None
        self.trades: List[Trade] = []
        self.equity_curve: List[Dict] = []
    
    def reset(self):
        """重置回测状态"""
        self.cash = self.initial_capital
        self.position = None
        self.trades = []
        self.equity_curve = []
    
    def _calculate_commission(self, amount: float) -> float:
        """计算手续费（A股最低5元）"""
        commission = amount * self.commission_rate
        return max(commission, 5.0)
    
    def _get_execution_price(self, price: float, order_type: OrderType) -> float:
        """计算实际成交价格（含滑点）"""
        if order_type == OrderType.BUY:
            return price * (1 + self.slippage)
        else:
            return price * (1 - self.slippage)
    
    def buy(self, symbol: str, date: datetime, price: float) -> Optional[Trade]:
        """买入"""
        if self.position is not None:
            return None  # 已有持仓，不重复买入
        
        # 计算可买入金额和股数
        available_cash = self.cash * self.position_size
        execution_price = self._get_execution_price(price, OrderType.BUY)
        shares = int(available_cash / execution_price / 100) * 100  # A股以手(100股)为单位
        
        if shares < 100:
            return None  # 资金不足
        
        amount = shares * execution_price
        commission = self._calculate_commission(amount)
        total_cost = amount + commission
        
        if total_cost > self.cash:
            shares = int((self.cash - 5) / execution_price / 100) * 100
            amount = shares * execution_price
            commission = self._calculate_commission(amount)
            total_cost = amount + commission
        
        # 执行买入
        self.cash -= total_cost
        self.position = Position(
            symbol=symbol,
            shares=shares,
            avg_cost=execution_price,
            current_price=execution_price,
            market_value=amount,
            pnl=0,
            pnl_pct=0
        )
        
        trade = Trade(
            date=date,
            symbol=symbol,
            order_type=OrderType.BUY,
            price=execution_price,
            shares=shares,
            amount=amount,
            commission=commission
        )
        self.trades.append(trade)
        
        return trade
    
    def sell(self, symbol: str, date: datetime, price: float) -> Optional[Trade]:
        """卖出"""
        if self.position is None:
            return None
        
        execution_price = self._get_execution_price(price, OrderType.SELL)
        amount = self.position.shares * execution_price
        commission = self._calculate_commission(amount)
        
        # 计算盈亏
        buy_amount = self.position.shares * self.position.avg_cost
        pnl = amount - buy_amount - commission
        
        # 执行卖出
        self.cash += amount - commission
        
        trade = Trade(
            date=date,
            symbol=symbol,
            order_type=OrderType.SELL,
            price=execution_price,
            shares=self.position.shares,
            amount=amount,
            commission=commission,
            pnl=pnl
        )
        self.trades.append(trade)
        
        self.position = None
        
        return trade
    
    def update_equity(self, date: datetime, price: float):
        """更新权益曲线"""
        if self.position:
            self.position.current_price = price
            self.position.market_value = self.position.shares * price
            self.position.pnl = self.position.market_value - self.position.shares * self.position.avg_cost
            self.position.pnl_pct = self.position.pnl / (self.position.shares * self.position.avg_cost)
            total_equity = self.cash + self.position.market_value
        else:
            total_equity = self.cash
        
        self.equity_curve.append({
            'date': date,
            'equity': total_equity,
            'cash': self.cash,
            'position_value': self.position.market_value if self.position else 0
        })
    
    def run(
        self,
        symbol: str,
        data: pd.DataFrame,
        signals: pd.DataFrame,
        strategy_name: str = "Unknown"
    ) -> BacktestResult:
        """
        运行回测
        
        Args:
            symbol: 股票代码
            data: 原始价格数据
            signals: 带有信号的数据
            strategy_name: 策略名称
        
        Returns:
            BacktestResult 回测结果
        """
        self.reset()
        
        # 合并数据和信号
        df = data.copy()
        df['signal'] = signals['signal'].values if 'signal' in signals.columns else 0
        
        for idx, row in df.iterrows():
            date = row['date']
            close_price = row['close']
            signal = row['signal']
            
            # 执行交易信号
            if signal == 1:  # 买入信号
                self.buy(symbol, date, close_price)
            elif signal == -1:  # 卖出信号
                self.sell(symbol, date, close_price)
            
            # 更新权益曲线
            self.update_equity(date, close_price)
        
        # 强制平仓
        if self.position:
            last_row = df.iloc[-1]
            self.sell(symbol, last_row['date'], last_row['close'])
        
        # 计算回测指标
        return self._calculate_result(symbol, strategy_name, df)
    
    def _calculate_result(
        self,
        symbol: str,
        strategy_name: str,
        data: pd.DataFrame
    ) -> BacktestResult:
        """计算回测结果指标"""
        equity_df = pd.DataFrame(self.equity_curve)
        equity_df['date'] = pd.to_datetime(equity_df['date'])
        equity_df = equity_df.set_index('date')
        
        # 基本指标
        initial_capital = self.initial_capital
        final_capital = equity_df['equity'].iloc[-1]
        total_return = (final_capital - initial_capital) / initial_capital
        
        # 年化收益
        days = (equity_df.index[-1] - equity_df.index[0]).days
        annual_return = (1 + total_return) ** (365 / max(days, 1)) - 1 if days > 0 else 0
        
        # 最大回撤
        equity_series = equity_df['equity']
        rolling_max = equity_series.expanding().max()
        drawdown = (equity_series - rolling_max) / rolling_max
        max_drawdown = drawdown.min()
        
        # 最大回撤持续天数
        max_dd_idx = drawdown.idxmin()
        peak_idx = equity_series[:max_dd_idx].idxmax()
        max_drawdown_duration = (max_dd_idx - peak_idx).days
        
        # 波动率（日收益率标准差，年化）
        daily_returns = equity_series.pct_change().dropna()
        volatility = daily_returns.std() * np.sqrt(252) if len(daily_returns) > 0 else 0
        
        # 夏普比率（假设无风险利率为3%）
        risk_free_rate = 0.03
        sharpe_ratio = (annual_return - risk_free_rate) / volatility if volatility > 0 else 0
        
        # 交易统计
        buy_trades = [t for t in self.trades if t.order_type == OrderType.BUY]
        sell_trades = [t for t in self.trades if t.order_type == OrderType.SELL]
        
        total_trades = len(sell_trades)
        win_trades = len([t for t in sell_trades if t.pnl > 0])
        loss_trades = len([t for t in sell_trades if t.pnl <= 0])
        win_rate = win_trades / total_trades if total_trades > 0 else 0
        
        # 盈亏比
        total_profit = sum([t.pnl for t in sell_trades if t.pnl > 0])
        total_loss = abs(sum([t.pnl for t in sell_trades if t.pnl <= 0]))
        profit_factor = total_profit / total_loss if total_loss > 0 else float('inf')
        
        return BacktestResult(
            symbol=symbol,
            strategy_name=strategy_name,
            start_date=data['date'].iloc[0],
            end_date=data['date'].iloc[-1],
            initial_capital=initial_capital,
            final_capital=final_capital,
            total_return=total_return,
            annual_return=annual_return,
            max_drawdown=max_drawdown,
            max_drawdown_duration=max_drawdown_duration,
            volatility=volatility,
            sharpe_ratio=sharpe_ratio,
            total_trades=total_trades,
            win_trades=win_trades,
            loss_trades=loss_trades,
            win_rate=win_rate,
            profit_factor=profit_factor,
            trades=self.trades,
            equity_curve=equity_df.reset_index()
        )
