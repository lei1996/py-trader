import argparse
import numpy as np
parser = argparse.ArgumentParser()
parser.add_argument('--symbol', help='品种代码 like: HT')
parser.add_argument('--max_cnt', help='最大开仓次数', type=int)
parser.add_argument('--direction', help='开仓方向 buy | sell')
parser.add_argument('--margin_call', help='跌 | 涨 x% 补仓, 0.01, 0.02, 0.03')
parser.add_argument('--close_call', help='获利多少平仓 0.01, 0.02, 0.03')
args = parser.parse_args()

symbol = args.symbol + '-USDT'
max_cnt = args.max_cnt
direction = args.direction
margin_call = np.array([item for item in args.margin_call.split(',')]).tolist()
close_call = np.array([item for item in args.close_call.split(',')]).tolist()

print(symbol)
print(type(max_cnt))
print(direction)
print(margin_call)
print(close_call)