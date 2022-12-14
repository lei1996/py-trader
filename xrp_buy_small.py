import time
import sys
import os
import numpy as np
from threading import Timer
from huobi.coin_swap.rest import account, market, order
from config.huobi import ACCESS_KEY, SECRET_KEY

close = 0
change = 0
max_cnt = 5
direction = 'buy'
margin_call = np.linspace(0, 0.01, num=5).tolist()
close_call = np.linspace(0.01, 0, num=5).tolist()
bs = [1, 2, 4, 8, 16, 32, 64, 128]
symbol = 'XRP-USD'


class RepeatTimer(Timer):
    def run(self):
        while not self.finished.wait(self.interval):
            self.function(*self.args, **self.kwargs)
        self.finished.set()
        print('Done')


class Martingale:
    def __init__(self, open_price, max_cnt, direction, bs, margin_call, close_call):
        self.max_cnt = max_cnt  # 最大补仓次数
        self.direction = direction  # 方向 buy 多 sell 空
        self.bs = bs  # 补仓数量 like: [1, 2, 4, 8]...
        self.margin_call = margin_call  # 跌 | 涨 1% 补仓
        self.close_call = close_call  # 获利多少平仓
        self.curr = 0  # 当前开仓次数

        self.price_lists = np.array([open_price])

        for i in range(1, max_cnt):
            if self.direction == 'buy':
                self.price_lists = np.append(
                    self.price_lists, self.price_lists[-1] - (self.price_lists[-1] * margin_call[i]))
            else:
                self.price_lists = np.append(
                    self.price_lists, self.price_lists[-1] + (self.price_lists[-1] * margin_call[i]))

    def is_add_open(self, price):  # 是否加仓
        if self.curr >= self.max_cnt:
            return []
        if self.direction == 'buy':
            return self.price_lists[self.price_lists >= price]
        else:
            return self.price_lists[self.price_lists <= price]

    def is_close_all(self, price):  # 是否平仓
        if self.curr == 0:
            return False

        result = 0
        for i in range(0, self.curr):
            result += self.price_lists[i] * self.bs[i]

        avg_price = result / sum(self.bs[:self.curr])

        if self.direction == 'buy':
            return price > (avg_price + (avg_price * self.close_call[self.curr - 1]))
        else:
            return price < (avg_price - (avg_price * self.close_call[self.curr - 1]))

    def curr_open(self):  # 当前开仓
        if self.curr == 0:
            return 0
        return sum(self.bs[:self.curr])


client = market.Market()
orderClient = order.Order(ACCESS_KEY,
                          SECRET_KEY)
accountClient = account.Account(ACCESS_KEY,
                                SECRET_KEY)


def fetchKLines(symbol: str, interval: str, limit: str):  # 通用请求k线函数
    return client.get_kline(
        {"contract_code": symbol, "period": interval, "size": limit})


def order(symbol: str, volume: int, offset: str, direction: str, price):  # 下单
    return orderClient.order(data={
        "contract_code": symbol,
        "volume": volume,
        "direction": direction,
        "offset": offset,
        # "price": close,
        "lever_rate": 50,
        "order_price_type": 'optimal_20'
    })


def fetchData():
    result = fetchKLines(symbol, '1min', '1')
    if len(result.get('data')) > 0:
        global close
        close = result.get('data')[0].get('close')
        print(f"update: {close}")


def fetchChangeData():
    items = fetchKLines(symbol, '15min', '5').get('data')

    sumValue = 0
    for item in items:
        sumValue += item.get('close')

    avg = sumValue / len(items)
    last = items[-1].get('close')
    global change

    change = ((last - avg) / avg) * 100
    print(f"avg: {avg}, last: {last}, change: {change}")


timer = RepeatTimer(3, fetchData, [])
timer.start()

changeTimer = RepeatTimer(5, fetchChangeData, [])
changeTimer.start()


time.sleep(10)

print(f"first: {close}")

if close == 0:
    timer.cancel()
    changeTimer.cancel()
    sys.exit(os.EX_OK)

martingale = Martingale(open_price=close, max_cnt=max_cnt,
                        direction=direction, bs=bs, margin_call=margin_call, close_call=close_call)


def main():
    print(f"close: {martingale.is_close_all(close)}, open: {len(martingale.is_add_open(close))}, curr: {martingale.curr}")
    if martingale.is_close_all(close) or abs(change) > 1:
        order_result = order(symbol=symbol, volume=int(martingale.curr_open()), offset='close',
                             direction=str(np.where(direction == 'buy', 'sell', 'buy')), price=close)
        print(f"close order_result: {order_result}")
        if order_result.get('status') == 'ok':
            timer.cancel()
            changeTimer.cancel()
            sys.exit(os.EX_OK)

    elif len(martingale.is_add_open(close)) > martingale.curr and abs(change) < 1:
        order_result = order(symbol=symbol, volume=martingale.bs[martingale.curr], offset='open',
                             direction=direction, price=close)
        print(
            f"open order_result: {order_result}, volume: {martingale.bs[martingale.curr]}")
        if order_result.get('status') == 'ok':
            martingale.curr += 1


print(accountClient.get_balance_valuation({"valuation_asset": 'USD'}))

print(martingale.price_lists)

print(int(martingale.curr_open()),  str(
    np.where(direction == 'buy', 'sell', 'buy')),)

mainTimer = RepeatTimer(3, main, [])
mainTimer.start()
mainTimer.join()
