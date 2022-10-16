import time
import sys
import os
import numpy as np
from threading import Timer
from huobi.linear_swap.rest import account, market, order
from config.linairx001 import ACCESS_KEY, SECRET_KEY

symbol = 'CLV-USDT'
max_cnt = 10
direction = 'buy'
margin_call = np.linspace(0, 0.02, num=max_cnt).tolist()
close_call = np.linspace(0.02, 0.01, num=max_cnt).tolist()
bs = [1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192][:max_cnt]
price_lists = np.array([])  # 开仓价格列表
close_lists = np.array([])  # 平仓价格列表
order_lists = []  # 订单列表
order_id = ''  # 平仓id
precision = 0  # 价格精度
curr = 0  # 当前开仓数

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
        "volume": volume,
        "direction": direction,
        "offset": offset,
        "price": price,
        "lever_rate": 10,
        "order_price_type": 'limit'
    })


def cross_cancel(symbol: str, order_id: str):  # 撤单
    print(
        f"symbol: {symbol}, order_id: {order_id}")
    return orderClient.cross_cancel({
        "order_id": order_id,
        "contract_code": symbol
    })


def cross_get_order_info(symbol: str, order_id: str):  # 查询订单状态
    print(
        f"symbol: {symbol}, order_id: {order_id}")
    return orderClient.cross_get_order_info({
        "order_id": order_id,
        "contract_code": symbol
    })


def fetchData():
    result = fetchKLines(symbol, '1min', '1')
    if len(result.get('data')) > 0:
        close = result.get('data')[0].get('close')
        print(f"update: {close}")
        return close


precision = get_contract_info(symbol=symbol)
print(f"价格精度 precision: {precision}")

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

for i in range(0, len(price_lists)):
    order_result = order(symbol=symbol, volume=bs[i], offset='open',
                         direction=direction, price=price_lists[i].round(precision))
    if order_result.get('status') == 'ok':
        order_lists.append(order_result.get('data').get('order_id_str'))

print(f"挂单列表: {order_lists}")


timer = RepeatTimer(5, fetchData, [])
timer.start()


time.sleep(5)


def main():  # 定时监控订单状态
    global curr, order_id

    if order_id != '':  # 查看平仓订单状态
        result = cross_get_order_info(symbol=symbol, order_id=order_id)
        if result.get('status') == 'ok':
            print(f"订单状态: {result.get('data')[0].get('status')}")
            if result.get('data')[0].get('status') == 6:
                for orderId in order_lists:
                    cancelRes = cross_cancel(symbol=symbol, order_id=orderId)
                    print(f"生命周期结束，撤掉之前的所有挂单: {cancelRes}, ")

                timer.cancel()
                sys.exit(os.EX_OK)

    cnt = 0
    for orderId in order_lists:
        result = cross_get_order_info(symbol=symbol, order_id=orderId)
        if result.get('status') == 'ok':
            print(f"订单状态: {result.get('data')[0].get('status')}")
            if result.get('data')[0].get('status') == 6:
                cnt += 1

    if cnt != curr:  # 如果有新的订单变更 需要重新挂单
        curr = cnt
        if order_id != '':
            cancelRes = cross_cancel(symbol=symbol, order_id=order_id)
            print(f"order_id 不为空 先撤单 {cancelRes}")

        orderRes = order(symbol=symbol, volume=sum(bs[:curr]), offset='close', direction=str(
            np.where(direction == 'buy', 'sell', 'buy')), price=close_lists[curr - 1].round(precision))
        print(f"close orderRes: {orderRes}, ")
        if orderRes.get('status') == 'ok':
            order_id = orderRes.get('data').get('order_id_str')


print(accountClient.get_balance_valuation({"valuation_asset": 'USD'}))


mainTimer = RepeatTimer(3, main, [])
mainTimer.start()
mainTimer.join()
