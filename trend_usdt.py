import os
import sys
import time
import argparse
import math
import numpy as np
from threading import Timer
from huobi.linear_swap.rest import account, market, order
from config.main import ACCESS_KEY, SECRET_KEY

parser = argparse.ArgumentParser()
parser.add_argument('--symbol', help='品种代码 like: HT')
parser.add_argument('--max_cnt', help='最大开仓次数', type=int)
parser.add_argument('--direction', help='开仓方向 buy | sell')
parser.add_argument('--margin_call', help='跌 | 涨 x% 补仓, 0.01, 0.02, 0.03')
parser.add_argument('--close_call', help='获利多少平仓 0.01, 0.02, 0.03')
parser.add_argument('--lever_rate', help='杠杆倍数', type=int, default=20)
args = parser.parse_args()

symbol = args.symbol + '-USDT'
max_cnt = args.max_cnt
direction = args.direction
lever_rate = args.lever_rate
margin_call = [float(item) for item in args.margin_call.split(',')]
close_call = [float(item) for item in args.close_call.split(',')]
bs = [1, 1, 1, 1, 1, 1, 64, 128, 256, 512, 1024, 2048, 4096, 8192][:max_cnt]
price_lists = np.array([])  # 开仓价格列表
close_lists = np.array([])  # 止损价格列表
precision = 0  # 价格精度
curr = 0  # 当前开仓数
base = 1


print(symbol)
print(max_cnt)
print(direction)
print(margin_call)
print(close_call)


client = market.Market()
orderClient = order.Order(ACCESS_KEY,
                          SECRET_KEY)
accountClient = account.Account(ACCESS_KEY,
                                SECRET_KEY)


class RepeatTimer(Timer):
    def run(self):
        while not self.finished.wait(self.interval):
            self.function(*self.args, **self.kwargs)
        self.finished.set()
        print('Done')


def get_contract_info(symbol: str):  # 从合约信息中获取 价格精度 数值
    result = client.get_contract_info({"contract_code": symbol})
    price_tick = str(result.get('data')[0].get('price_tick'))

    if '1e-' in price_tick:
        return int(price_tick.split('-')[1])
    else:
        return len(price_tick.split('.')[1])


def fetchKLines(symbol: str, interval: str, limit: str):  # 通用请求k线函数
    return client.get_kline(
        {"contract_code": symbol, "period": interval, "size": limit})


def order(symbol: str, volume: int, offset: str, direction: str):  # 下单
    print(
        f"symbol: {symbol}, volume: {volume}, offset: {offset}, direction: {direction}")
    return orderClient.cross_order({
        "contract_code": symbol,
        "volume": volume * base,
        "direction": direction,
        "offset": offset,
        "lever_rate": lever_rate,
        "order_price_type": 'optimal_20'
    })


def cross_get_order_info(symbol: str, order_id: str):  # 查询订单状态
    print(
        f"查询订单状态 symbol: {symbol}, order_id: {order_id}")
    return orderClient.cross_get_order_info({
        "order_id": order_id,
        "contract_code": symbol
    })


def fetchData():
    result = fetchKLines(symbol, '1min', '1')
    if not result == None and len(result.get('data')) > 0:
        close = result.get('data')[0].get('close')
        print(f"update: {close}")
        return close


precision = get_contract_info(symbol=symbol)
print(f"价格精度 precision: {precision}")

balanceRes = accountClient.get_balance_valuation({"valuation_asset": 'USD'})
print(f"当前权益: {balanceRes}")


if not balanceRes == None and balanceRes.get('status') == 'ok':
    x = math.floor(float(balanceRes.get('data')[0].get('balance')) / 100)
    base = (1 if x == 0 else x) * 1
    print(f"base: {base}")

close = fetchData()

print(f"first: {close}")

if close == 0:
    sys.exit(os.EX_OK)

price_lists = np.array([close])


for i in range(1, max_cnt):
    if direction == 'buy':
        price_lists = np.append(
            price_lists, price_lists[-1] + (price_lists[-1] * margin_call[i]))
    else:
        price_lists = np.append(
            price_lists, price_lists[-1] - (price_lists[-1] * margin_call[i]))

print(f"开仓价格列表: {price_lists}")

for i in range(0, max_cnt):
    open_price = price_lists[i]
    if direction == 'buy':
        close_lists = np.append(
            close_lists, open_price - (open_price * close_call[i]))
    else:
        close_lists = np.append(
            close_lists, open_price + (open_price * close_call[i]))

print(f"止损价格列表: {close_lists}")


def main():  # 定时监控订单状态
    global curr
    close = fetchData()
    print(
        f"当前状态, curr: {curr}, close: {close}, 当前开仓价格: {price_lists[curr]}, 上一次开仓价格: {price_lists[curr - 1]}, 当前止损价格: {close_lists[curr - 1]}")

    if close == None:
        return

    isClose = False  # 是否平仓
    if curr == max_cnt - 1:  # 到达列表尾端

        if direction == 'buy' and price_lists[curr] <= close:  # 多头头寸
            print(
                f"到达列表尾端，多头满足获利平仓条件, 当前价格: {close}, 止盈触发价格: {price_lists[curr]}")
            isClose = True

        elif direction == 'sell' and price_lists[curr] >= close:  # 空头头寸
            print(
                f"到达列表尾端，空头满足获利平仓条件, 当前价格: {close}, 止盈触发价格: {price_lists[curr]}")
            isClose = True

    if curr != 0:
        # 多/空 头寸 止损
        if direction == 'buy' and close_lists[curr - 1] >= close:
            print(f"多头触发止损条件, 当前价格: {close}, 止损触发价格: {close_lists[curr - 1]}")
            isClose = True

        elif direction == 'sell' and close_lists[curr - 1] <= close:
            print(f"空头触发止损条件, 当前价格: {close}, 止损触发价格: {close_lists[curr - 1]}")
            isClose = True

    if isClose == True:
        orderRes = order(symbol=symbol, volume=sum(bs[:curr]), offset='close', direction=str(
            np.where(direction == 'buy', 'sell', 'buy')))
        print(f"平仓 订单: {orderRes}, ")
        if not orderRes == None and orderRes.get('status') == 'ok':
            close_order_id = orderRes.get('data').get('order_id_str')
            time.sleep(2)  # 等待 2s
            orderResult = cross_get_order_info(
                symbol=symbol, order_id=close_order_id)
            if not orderResult == None and orderResult.get('status') == 'ok':
                print(f"订单状态: {orderResult.get('data')[0].get('status')}")
                if orderResult.get('data')[0].get('status') == 6:
                    sys.exit(os.EX_OK)

    # 多/空 头寸 开仓
    if (direction == 'buy' and price_lists[curr] <= close) or (direction == 'sell' and price_lists[curr] >= close):
        orderRes = order(
            symbol=symbol, volume=bs[curr], offset='open', direction=direction)
        print(f"开仓 订单: {orderRes}, ")
        if not orderRes == None and orderRes.get('status') == 'ok':
            open_order_id = orderRes.get('data').get('order_id_str')
            time.sleep(2)  # 等待 2s
            orderResult = cross_get_order_info(
                symbol=symbol, order_id=open_order_id)
            if not orderResult == None and orderResult.get('status') == 'ok':
                print(f"订单状态: {orderResult.get('data')[0].get('status')}")
                if orderResult.get('data')[0].get('status') == 6:
                    curr += 1


mainTimer = RepeatTimer(5, main, [])
mainTimer.start()
mainTimer.join()
