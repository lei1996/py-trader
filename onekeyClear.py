
from huobi.linear_swap.rest import account, market, order
from config.linairx001 import ACCESS_KEY, SECRET_KEY


client = market.Market()
orderClient = order.Order(ACCESS_KEY,
                          SECRET_KEY)
accountClient = account.Account(ACCESS_KEY,
                                SECRET_KEY)


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

def cross_cancel_all(symbol: str):  # 撤单
    print(
        f"全部撤单 symbol: {symbol}")
    return orderClient.cross_cancel_all({
        "contract_code": symbol
    })


def cross_get_position_info():  # 当前用户持仓
    print(
        f"当前品种")
    return accountClient.cross_get_position_info({
    })


position = cross_get_position_info()
print(f"position: {position}")
if not position == None and len(position.get('data')) > 0:
    for item in position.get('data'):
        cancel = cross_cancel_all(symbol=item.get('contract_code'))
        print(f"撤单返回值: {cancel}")
        ordRes = order(symbol=item.get('contract_code'), volume=int(item.get(
            'volume')),  offset='close', direction='sell' if item.get('direction') == 'buy' else 'buy', lever_rate=item.get('lever_rate'))
        print(f"平仓订单返回值: {ordRes}")
