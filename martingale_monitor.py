import subprocess
import json
from threading import Timer
from huobi.linear_swap.rest import account, market, order
from config.linairx001 import ACCESS_KEY, SECRET_KEY

direction = ['buy', 'sell']
symbols = [{
    "symbol": 'doge',
    "lever_rate": '75'
}, {
    "symbol": 'fil',
    "lever_rate": '75'
}, {
    "symbol": 'clv',
    "lever_rate": '20'
}, {
    "symbol": '1inch',
    "lever_rate": '50'
}, {
    "symbol": 'dot',
    "lever_rate": '75'
}, {
    "symbol": 'snx',
    "lever_rate": '50'
}]


class RepeatTimer(Timer):
    def run(self):
        while not self.finished.wait(self.interval):
            self.function(*self.args, **self.kwargs)
        self.finished.set()
        print('Done')


client = market.Market()
orderClient = order.Order(ACCESS_KEY,
                          SECRET_KEY)
accountClient = account.Account(ACCESS_KEY,
                                SECRET_KEY)


def fetchKLines(symbol: str, interval: str, limit: str):  # 通用请求k线函数
    return client.get_kline(
        {"contract_code": symbol, "period": interval, "size": limit})


def order(symbol: str, volume: int, offset: str, direction: str, lever_rate: int):  # 下单
    print(
        f"全部 平仓 symbol: {symbol}, volume: {volume}, offset: {offset}, direction: {direction}")
    return orderClient.cross_order({
        "contract_code": symbol,
        "volume": volume,
        "direction": direction,
        "offset": offset,
        "lever_rate": lever_rate,
        "order_price_type": 'optimal_20'
    })


def cross_get_position_info(symbol: str):  # 当前用户持仓
    print(
        f"当前品种 symbol: {symbol}")
    return accountClient.cross_get_position_info({
        "contract_code": symbol
    })


def cross_cancel_all(symbol: str):  # 撤单
    print(
        f"全部撤单 symbol: {symbol}")
    return orderClient.cross_cancel_all({
        "contract_code": symbol
    })


def pm2_status():
    out = subprocess.run('pm2 jlist', stdout=subprocess.PIPE, shell=True)
    result = {}

    for item in json.loads(out.stdout):
        # print(item.get('name'), item.get('pm2_env').get('status'))
        result[item.get('name')] = item.get('pm2_env').get('status')

    return result


def run_task(name: str, symbol: str, max_cnt: str, direction: str, lever_rate: str, margin_call: str, close_call: str, access_key: str, secret_key: str):
    pm2 = pm2_status()
    print(f"pm2: {pm2}")
    if not pm2.get(name) == None:
        return

    print('启动任务', name, symbol.upper(), max_cnt, direction,
          lever_rate, margin_call, close_call, access_key, secret_key)

    subprocess.run(['pm2',
                    'start',
                    './martingale_usdt.py',
                    '--name',
                    name,
                    '--interpreter',
                    'python3',
                    '--',
                    '--symbol',
                    symbol.upper(),
                    '--max_cnt',
                    str(max_cnt),
                    '--direction',
                    direction,
                    '--lever_rate',
                    str(lever_rate),
                    '--margin_call',
                    margin_call,
                    '--close_call',
                    close_call,
                    '--access_key',
                    access_key,
                    '--secret_key',
                    secret_key, ])


def stop_task(name: str, symbol: str):  # 终止任务
    pm2 = pm2_status()
    if pm2.get(name) == None:
        return

    subprocess.run(['pm2', 'delete', name])  # pm2 删除任务
    cancelAllRes = cross_cancel_all(
        symbol=symbol.upper() + '-USDT')
    print(f"撤销该品种所有挂单: {cancelAllRes}")
    position = cross_get_position_info(symbol.upper() + '-USDT')
    print(f"position: {position}")
    if not position == None and len(position.get('data')) > 0:
        for item in position.get('data'):
            ordRes = order(symbol=item.get('contract_code'), volume=int(item.get(
                'volume')),  offset='close', direction='sell' if item.get('direction') == 'buy' else 'buy', lever_rate=item.get('lever_rate'))
            print(f"平仓订单返回值: {ordRes}")


def main(symbol: str, lever_rate: str):
    result = fetchKLines(
        symbol=f"{symbol.upper()}-USDT", interval='15min', limit='96')

    # print(result)
    max_index = 0
    min_index = 0
    klines = []

    if result == None or len(result.get('data')) == 0:
        return

    klines = result.get('data')
    print(f"当前k线len {len(klines)}")

    for i in range(1, len(klines)):
        max_index = max_index if klines[max_index].get(
            'high') > klines[i].get('high') else i
        min_index = min_index if klines[min_index].get(
            'low') < klines[i].get('low') else i

    print(f"max: {klines[max_index]}, min: {klines[min_index]}")
    print(f"max_index: {max_index}, min_index: {min_index}")

    high = klines[max_index].get('high')
    low = klines[min_index].get('low')
    middle = ((high - low) / 2) + low

    change = ((high - low) / low) * 100

    print(f"change: {change}")
    print(f"middle: {middle}")
    print(f"last: {klines[-1]}")

    if change > 5:
        if max_index - min_index >= 6:  # 最大值和最小值的间隔必须要大于6根k线，过滤急拉急跌的行情
            maxv = max_index
            minv = max_index
            isOpen = False
            if len(klines) == max_index + 1:
                print('当前k线就是最大值，直接开启马丁')
                isOpen = True
            else:
                for i in range(max_index + 1, len(klines)):
                    # print(klines[i])
                    maxv = maxv if klines[maxv].get(
                        'high') > klines[i].get('high') else i
                    minv = minv if klines[minv].get(
                        'low') < klines[i].get('low') else i

                print(f"maxv: {maxv}, minv: {minv}")
                print(
                    f"maxv_kline: {klines[maxv]}, minv_kline: {klines[minv]}")
                se_high = klines[maxv].get('high')
                se_low = klines[minv].get('low')
                se_change = ((se_high - se_low) / se_low) * 100
                print(f"se_change: {se_change}")

                if se_change / change <= 1/2:
                    print(f'次级振幅小于{change / 2}%， 开启多头马丁')
                    isOpen = True

            if isOpen == True:
                print('开启马丁~~~~')
                run_task(name=f"{symbol}_buy_martingale", symbol=symbol, max_cnt=5, direction='buy', lever_rate=lever_rate,
                         margin_call='0.0,0.01,0.01,0.01,0.01', close_call='0.05,0.03,0.02,0.01,0.00', access_key=ACCESS_KEY, secret_key=SECRET_KEY)
            elif isOpen == False:
                print('未满足条件, 终止马丁')
                stop_task(name=f"{symbol}_buy_martingale",
                          symbol=symbol)
        else:
            print('未知情况，终止交易')
            stop_task(name=f"{symbol}_buy_martingale",
                      symbol=symbol)

    elif change <= 5:
        print('震荡行情，关闭多/空马丁')
        stop_task(name=f"{symbol}_buy_martingale",
                  symbol=symbol)


for item in symbols:
    symbol, lever_rate = item.values()
    print(f'服务运行中: symbol: {symbol}, lever_rate: {lever_rate}')
    main(symbol, int(lever_rate))
