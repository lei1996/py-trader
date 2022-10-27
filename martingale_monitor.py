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
# symbols = [{
#     "symbol": 'shib',
#     "lever_rate": '10'
# }, {
#     "symbol": 'icp',
#     "lever_rate": '10'
# }]


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
        print(item.get('name'), item.get('pm2_env').get('status'))
        result[item.get('name')] = item.get('pm2_env').get('status')

    return result


def fetchData(symbol: str, lever_rate: int):
    print(symbol, lever_rate)
    result = fetchKLines(symbol.upper() + '-USDT', '60min', '24')

    if not result == None and len(result.get('data')) > 0:
        klines = result.get('data')
        maxv = float('-inf')
        minv = float('inf')
        print(f"当前k线len {len(klines)}")
        for kline in klines:
            maxv = max(maxv, kline.get('high'))
            minv = min(minv, kline.get('low'))

        print(f"maxv: {maxv}, minv: {minv}")
        pm2st = pm2_status()
        print(pm2st)

        change = ((maxv - minv) / minv) * 100
        if change > 5:
            print('当前品种24小时振幅大于 5%, 终止该品种服务')
            for dn in direction:
                if pm2st.get(symbol + '_' + dn + '_martingale') == 'online':
                    subprocess.run(
                        ['pm2', 'stop', symbol + '_' + dn + '_martingale'])
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

        else:
            print('当前品种24小时振幅小于 5%, 启动该品种服务')
            for dn in direction:
                if not pm2st.get(symbol + '_' + dn + '_martingale') == 'online':
                    subprocess.run(
                        ['pm2', 'restart', symbol + '_' + dn + '_martingale'])

        print(f"当前{symbol} @change 振幅: {change}")


for item in symbols:
    symbol, lever_rate = item.values()
    fetchData(symbol, int(lever_rate))


# 每小时执行一次
# 24小时振幅大于 5% pm2 stop xxx_buy xxx_sell && 撤销所有订单 && 平仓该品种
# 小于 5% pm2 restart xxx_buy xxx_sell
