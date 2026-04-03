"""
量化交易系统主程序
"""

import os
import sys
import yaml
import argparse
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.fetcher import DataFetcher
from strategies import get_strategy, STRATEGY_REGISTRY
from backtest.engine import BacktestEngine
from utils.visualizer import Visualizer, print_result_summary


def load_config(config_path: str) -> dict:
    """加载配置文件"""
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def run_single_stock(
    symbol: str,
    config: dict,
    fetcher: DataFetcher,
    engine: BacktestEngine,
    visualizer: Visualizer
):
    """运行单只股票的回测"""
    print(f"\n{'='*50}")
    print(f"正在处理: {symbol}")
    print('='*50)
    
    # 获取数据
    print("  [1/4] 获取数据...")
    data = fetcher.get_stock_data(
        symbol,
        config['date']['start_date'],
        config['date']['end_date']
    )
    
    if data.empty:
        print(f"  股票 {symbol} 数据获取失败，跳过")
        return None
    
    print(f"  获取到 {len(data)} 条数据")
    
    # 初始化策略
    print("  [2/4] 初始化策略...")
    strategy = get_strategy(
        config['strategy']['name'],
        config['strategy']['params']
    )
    print(f"  使用策略: {strategy}")
    
    # 生成信号
    print("  [3/4] 生成交易信号...")
    signals = strategy.generate_signals(data)
    buy_signals = len(signals[signals['signal'] == 1])
    sell_signals = len(signals[signals['signal'] == -1])
    print(f"  买入信号: {buy_signals} 次, 卖出信号: {sell_signals} 次")
    
    # 运行回测
    print("  [4/4] 运行回测...")
    result = engine.run(
        symbol=symbol,
        data=data,
        signals=signals,
        strategy_name=strategy.name
    )
    
    # 打印结果
    print_result_summary(result)
    
    # 生成图表
    results_dir = config['data']['save_path'].replace('./data', './results')
    os.makedirs(results_dir, exist_ok=True)
    
    visualizer.plot_equity_curve(
        result,
        save_path=os.path.join(results_dir, f'{symbol}_equity.png'),
        show=False
    )
    
    visualizer.plot_trades(
        result,
        data,
        save_path=os.path.join(results_dir, f'{symbol}_trades.png'),
        show=False
    )
    
    return result


def run_multi_stocks(config: dict):
    """运行多只股票的回测"""
    fetcher = DataFetcher(config['data']['save_path'])
    engine = BacktestEngine(
        initial_capital=config['backtest']['initial_capital'],
        commission_rate=config['backtest']['commission_rate'],
        slippage=config['backtest']['slippage'],
        position_size=config['backtest']['position_size']
    )
    visualizer = Visualizer()
    
    results = []
    for symbol in config['stocks']:
        result = run_single_stock(symbol, config, fetcher, engine, visualizer)
        if result:
            results.append(result)
    
    # 策略比较
    if len(results) > 1:
        print("\n" + "="*60)
        print("策略综合比较")
        print("="*60)
        
        for r in results:
            print(f"  {r.symbol}: 年化收益 {r.annual_return*100:+.2f}%, "
                  f"最大回撤 {r.max_drawdown*100:.2f}%, "
                  f"夏普比率 {r.sharpe_ratio:.2f}")
        
        # 绘制比较图
        results_dir = config['data']['save_path'].replace('./data', './results')
        visualizer.compare_strategies(
            results,
            save_path=os.path.join(results_dir, 'strategy_comparison.png'),
            show=False
        )
    
    return results


def compare_different_strategies(
    symbol: str,
    config: dict,
    strategies: list
):
    """比较不同策略在同一只股票上的表现"""
    fetcher = DataFetcher(config['data']['save_path'])
    visualizer = Visualizer()
    
    data = fetcher.get_stock_data(
        symbol,
        config['date']['start_date'],
        config['date']['end_date']
    )
    
    if data.empty:
        print(f"股票 {symbol} 数据获取失败")
        return
    
    results = []
    
    for strategy_name in strategies:
        print(f"\n测试策略: {strategy_name}")
        print("-"*40)
        
        # 获取策略默认参数
        if strategy_name in ['ma_cross', 'ema_cross']:
            params = config['strategy']['params']
        elif strategy_name == 'rsi':
            params = {
                'rsi_period': config['strategy']['params'].get('rsi_period', 14),
                'oversold': config['strategy']['params'].get('rsi_oversold', 30),
                'overbought': config['strategy']['params'].get('rsi_overbought', 70)
            }
        else:
            params = {}
        
        strategy = get_strategy(strategy_name, params)
        signals = strategy.generate_signals(data)
        
        engine = BacktestEngine(
            initial_capital=config['backtest']['initial_capital'],
            commission_rate=config['backtest']['commission_rate'],
            slippage=config['backtest']['slippage'],
            position_size=config['backtest']['position_size']
        )
        
        result = engine.run(
            symbol=symbol,
            data=data,
            signals=signals,
            strategy_name=strategy.name
        )
        
        results.append(result)
        print_result_summary(result)
    
    # 绘制策略比较图
    results_dir = config['data']['save_path'].replace('./data', './results')
    os.makedirs(results_dir, exist_ok=True)
    
    visualizer.compare_strategies(
        results,
        save_path=os.path.join(results_dir, f'{symbol}_strategies_comparison.png'),
        show=False
    )
    
    return results


def main():
    parser = argparse.ArgumentParser(description='A股量化交易回测系统')
    parser.add_argument(
        '-c', '--config',
        default='config.yaml',
        help='配置文件路径 (默认: config.yaml)'
    )
    parser.add_argument(
        '-s', '--stock',
        help='单只股票代码 (如: 000001)'
    )
    parser.add_argument(
        '--compare-strategies',
        action='store_true',
        help='比较不同策略'
    )
    parser.add_argument(
        '--list-strategies',
        action='store_true',
        help='列出所有可用策略'
    )
    
    args = parser.parse_args()
    
    # 列出策略
    if args.list_strategies:
        print("\n可用策略列表:")
        print("-"*40)
        for name, cls in STRATEGY_REGISTRY.items():
            print(f"  {name}: {cls.__doc__ or cls.__name__}")
        return
    
    # 加载配置
    config_path = os.path.join(os.path.dirname(__file__), args.config)
    config = load_config(config_path)
    
    print("\n" + "="*60)
    print("A股量化交易回测系统")
    print("="*60)
    print(f"配置文件: {args.config}")
    print(f"策略: {config['strategy']['name']}")
    print(f"回测区间: {config['date']['start_date']} ~ {config['date']['end_date']}")
    print(f"初始资金: {config['backtest']['initial_capital']:,.0f} 元")
    print("="*60)
    
    if args.compare_strategies:
        # 比较不同策略
        symbol = args.stock or config['stocks'][0]
        strategies = ['ma_cross', 'ema_cross', 'rsi']
        compare_different_strategies(symbol, config, strategies)
    elif args.stock:
        # 单只股票
        fetcher = DataFetcher(config['data']['save_path'])
        engine = BacktestEngine(
            initial_capital=config['backtest']['initial_capital'],
            commission_rate=config['backtest']['commission_rate'],
            slippage=config['backtest']['slippage'],
            position_size=config['backtest']['position_size']
        )
        visualizer = Visualizer()
        run_single_stock(args.stock, config, fetcher, engine, visualizer)
    else:
        # 多只股票
        run_multi_stocks(config)
    
    print("\n回测完成! 结果已保存到 results/ 目录")


if __name__ == '__main__':
    main()
