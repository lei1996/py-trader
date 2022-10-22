import subprocess

direction = ['buy', 'sell']
symbols = [{
    "symbol": 'btc',
    "lever_rate": '200'
}, {
    "symbol": 'eth',
    "lever_rate": '200'
}, {
    "symbol": 'clv',
    "lever_rate": '20'
}, {
    "symbol": 'dydx',
    "lever_rate": '50'
}, {
    "symbol": 'ht',
    "lever_rate": '20'
}, {
    "symbol": 'apt',
    "lever_rate": '10'
}, ]

for item in symbols:
    for dn in direction:
        symbol, lever_rate = item.values()
        subprocess.run(['pm2',
                        'start',
                        './martingale_usdt.py',
                        '--name',
                        symbol + '_' + dn,
                        '--interpreter',
                        'python3',
                        '--',
                        '--symbol',
                        symbol.upper(),
                        '--max_cnt',
                        '5',
                        '--direction',
                        dn,
                        '--lever_rate',
                        lever_rate,
                        '--margin_call',
                        '0.0,0.0025,0.005,0.0075,0.01',
                        '--close_call',
                        '0.05,0.04,0.03,0.02,0.01'])
