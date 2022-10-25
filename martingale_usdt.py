import os
import sys
import time
import argparse
import math
import numpy as np
from threading import Timer
from huobi.linear_swap.rest import account, market, order
from config.linairx001 import ACCESS_KEY, SECRET_KEY

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
bs = [1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192][:max_cnt]
price_lists = np.array([])  # 开仓价格列表
close_lists = np.array([])  # 平仓价格列表
open_order_id = ''  # 开仓订单id
close_order_id = ''  # 平仓id
precision = 0  # 价格精度
curr = 0  # 当前开仓数
base = 5
isMax = False  # 是否开仓到了尾端
ratio = 1


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


def order(symbol: str, volume: int, offset: str, direction: str, price):  # 下单
    print(
        f"symbol: {symbol}, volume: {volume}, offset: {offset}, direction: {direction}")
    return orderClient.cross_order({
        "contract_code": symbol,
        "volume": volume * base * ratio,
        "direction": direction,
        "offset": offset,
        "price": price,
        "lever_rate": lever_rate,
        "order_price_type": 'limit'
    })


def cross_cancel(symbol: str, order_id: str):  # 撤单
    print(
        f"撤单 symbol: {symbol}, order_id: {order_id}")
    return orderClient.cross_cancel({
        "order_id": order_id,
        "contract_code": symbol
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

balance = accountClient.get_balance_valuation({"valuation_asset": 'USD'})
print(f"当前权益: {balance}")


if not balanceRes == None and balanceRes.get('status') == 'ok':
    ratio = math.floor(float(balanceRes.get('data')[0].get('balance')) / 100)
    print(f"ratio: {ratio}")

close = fetchData()

print(f"first: {close}")

if close == 0:
    sys.exit(os.EX_OK)

price_lists = np.array([close])


for i in range(1, max_cnt):
    if direction == 'buy':
        price_lists = np.append(
            price_lists, price_lists[-1] - (price_lists[-1] * margin_call[i]))
    else:
        price_lists = np.append(
            price_lists, price_lists[-1] + (price_lists[-1] * margin_call[i]))

print(f"开仓价格列表: {price_lists}")

result = 0
for i in range(0, max_cnt):
    result += price_lists[i] * bs[i]
    avg = result / sum(bs[:i+1])
    if direction == 'buy':
        close_lists = np.append(
            close_lists, avg + (avg * close_call[i]))
    else:
        close_lists = np.append(
            close_lists, avg - (avg * close_call[i]))

print(f"平仓价格列表: {close_lists}")

order_result = order(symbol=symbol, volume=bs[curr], offset='open',
                     direction=direction, price=price_lists[curr].round(precision))
if not order_result == None and order_result.get('status') == 'ok':
    open_order_id = order_result.get('data').get('order_id_str')
    curr += 1

print(f"第一次挂单: {order_result}, 挂单id: {open_order_id}")


timer = RepeatTimer(5, fetchData, [])
timer.start()


time.sleep(5)


def main():  # 定时监控订单状态
    global curr, open_order_id, close_order_id, isMax
    print(
        f"当前状态, curr: {curr}, open_order_id: {open_order_id}, close_order_id: {close_order_id}")

    if close_order_id != '':  # 查看平仓订单状态
        result = cross_get_order_info(symbol=symbol, order_id=close_order_id)
        if not result == None and result.get('status') == 'ok':
            print(f"订单状态: {result.get('data')[0].get('status')}")
            if result.get('data')[0].get('status') == 6:
                cancelRes = cross_cancel(symbol=symbol, order_id=open_order_id)
                print(f"生命周期结束，撤掉之前的开仓挂单: {cancelRes}, ")

                timer.cancel()
                sys.exit(os.EX_OK)

    if isMax == True:
        return

    orderResult = cross_get_order_info(symbol=symbol, order_id=open_order_id)
    if not orderResult == None and orderResult.get('status') == 'ok':
        print(f"订单状态: {orderResult.get('data')[0].get('status')}")
        if orderResult.get('data')[0].get('status') == 6:
            if close_order_id != '':
                cancelRes = cross_cancel(
                    symbol=symbol, order_id=close_order_id)
                print(f"close_order_id 不为空 先撤单 {cancelRes}")
            orderRes = order(symbol=symbol, volume=sum(bs[:curr]), offset='close', direction=str(
                np.where(direction == 'buy', 'sell', 'buy')), price=close_lists[curr - 1].round(precision))
            print(f"平仓 订单挂单: {orderRes}, ")
            if not orderRes == None and orderRes.get('status') == 'ok':
                close_order_id = orderRes.get('data').get('order_id_str')
                if curr == max_cnt:
                    isMax = True

            if curr < max_cnt:
                order_result = order(symbol=symbol, volume=bs[curr], offset='open',
                                     direction=direction, price=price_lists[curr].round(precision))
                if not order_result == None and order_result.get('status') == 'ok':
                    open_order_id = order_result.get(
                        'data').get('order_id_str')
                print(f"重新挂开仓单: {order_result}, 挂单id: {open_order_id}")
                curr += 1


mainTimer = RepeatTimer(10, main, [])
mainTimer.start()
mainTimer.join()
