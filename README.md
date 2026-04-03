# A股量化交易系统 (Quant Trader)

一个简单实用的A股量化交易回测框架，支持多种交易策略，适合量化交易入门学习。

## 功能特点

- **数据获取**: 使用 akshare 获取A股历史数据，支持本地缓存
- **交易策略**: 内置双均线、RSI等多种策略，易于扩展
- **回测引擎**: 完整的交易模拟，支持手续费和滑点
- **风险分析**: 最大回撤、夏普比率等风险评估指标
- **可视化**: 权益曲线、交易信号、策略对比图表

## 项目结构

```
quant_trader/
├── config.yaml          # 配置文件
├── main.py              # 主程序入口
├── requirements.txt     # 依赖包
├── data/               # 数据模块
│   └── fetcher.py      # 数据获取
├── strategies/         # 策略模块
│   ├── base.py         # 策略基类
│   ├── ma_cross.py     # 均线策略
│   └── rsi.py          # RSI策略
├── backtest/           # 回测模块
│   └── engine.py       # 回测引擎
├── utils/              # 工具模块
│   └── visualizer.py   # 可视化
├── logs/               # 日志目录
└── results/            # 回测结果
```

## 安装

```bash
# 克隆仓库
git clone https://github.com/Andrew-Pei/quant_trader.git
cd quant_trader

# 安装依赖
pip install -r requirements.txt
```

## 快速开始

### 1. 修改配置文件

编辑 `config.yaml` 设置股票池、策略参数等：

```yaml
# 股票池
stocks:
  - "000001"  # 平安银行
  - "600519"  # 贵州茅台

# 日期配置
date:
  start_date: "20230101"
  end_date: "20240101"
```

### 2. 运行回测

```bash
# 回测配置文件中的所有股票
python main.py

# 回测单只股票
python main.py -s 000001

# 比较不同策略
python main.py -s 000001 --compare-strategies

# 查看可用策略
python main.py --list-strategies
```

### 3. 查看结果

回测完成后，结果保存在 `results/` 目录：
- `{股票代码}_equity.png` - 权益曲线
- `{股票代码}_trades.png` - 交易信号
- `strategy_comparison.png` - 策略对比

## 可用策略

| 策略名称 | 说明 |
|---------|------|
| `ma_cross` | 双均线交叉策略（金叉买入，死叉卖出）|
| `ema_cross` | 指数均线交叉策略 |
| `rsi` | RSI超买超卖策略 |
| `rsi_divergence` | RSI背离策略 |

## 自定义策略

继承 `BaseStrategy` 类实现自己的策略：

```python
from strategies.base import BaseStrategy, Signal

class MyStrategy(BaseStrategy):
    def __init__(self, params=None):
        default_params = {'period': 20}
        if params:
            default_params.update(params)
        super().__init__(default_params)
    
    def generate_signals(self, data):
        df = data.copy()
        df['signal'] = Signal.HOLD.value
        
        # 实现你的交易逻辑
        # ...
        
        return df
    
    def get_required_data_length(self):
        return self.params['period'] + 1
```

## 回测指标说明

| 指标 | 说明 |
|-----|------|
| 总收益率 | 整个回测期间的收益百分比 |
| 年化收益 | 换算成年度的收益率 |
| 最大回撤 | 从峰值到谷值的最大跌幅 |
| 夏普比率 | 风险调整后收益 (越高越好) |
| 胜率 | 盈利交易占比 |
| 盈亏比 | 总盈利/总亏损 |

## 注意事项

1. 本系统仅用于学习和研究目的
2. 历史数据不代表未来收益
3. 实盘交易需谨慎，注意风险控制
4. A股交易规则：T+1、涨跌停限制等

## 依赖

- akshare >= 1.12.0 (数据获取)
- pandas >= 2.0.0
- numpy >= 1.24.0
- matplotlib >= 3.7.0
- pyyaml >= 6.0

## License

MIT License

## 作者

Andrew-Pei - 信息科技教师 / 量化交易爱好者
