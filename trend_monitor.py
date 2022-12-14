import subprocess
import json
from threading import Timer
from huobi.linear_swap.rest import account, market, order
from config.main import ACCESS_KEY, SECRET_KEY

Name = '_trend'
direction = ['buy', 'sell']


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


def get_contract_info():  # 获取合约信息和杠杆倍数
    contract_info = accountClient.cross_get_available_level_rate({})
    result = []
    if not contract_info == None and len(contract_info.get('data')) > 0:
        for item in contract_info.get('data'):
            result.append({
                "symbol": item.get('contract_code').split('-')[0].lower(),
                "level_rate": item.get('available_level_rate').split(',')[-1]
            })
    print(result)
    return result


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


def has_task(pm2, name: str):  # 存在该类型任务的计数
    cnt = 0

    for key in pm2:
        if name in key:
            cnt += 1

    return cnt


def run_task(name: str, symbol: str, max_cnt: str, direction: str, lever_rate: str, margin_call: str, close_call: str, access_key: str, secret_key: str):
    pm2 = pm2_status()
    cnt = has_task(pm2, Name)
    print(f"pm2: {pm2}, {Name} cnt: {cnt}")

    if not pm2.get(name) == None or cnt >= 20:
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
    if not pm2.get(name) == None:
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

    if change < 3:
        print('开启马丁~~~~')
        for dn in direction:
            run_task(name=f"{symbol}_{dn}{Name}", symbol=symbol, max_cnt=5, direction=dn, lever_rate=lever_rate,
                     margin_call='0.0,0.0025,0.005,0.0075,0.01', close_call='0.01,0.0075,0.005,0.0025,0.0', access_key=ACCESS_KEY, secret_key=SECRET_KEY)

    else:
        print(f'change 大于 {change}, 关闭多/空马丁')
        for dn in direction:
            stop_task(name=f"{symbol}_{dn}{Name}", symbol=symbol)


symbols = get_contract_info()

for item in symbols:
    symbol, lever_rate = item.values()
    print(f'服务运行中: symbol: {symbol}, lever_rate: {lever_rate}')
    main(symbol, int(lever_rate))
