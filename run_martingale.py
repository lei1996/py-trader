import subprocess

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
}, ]

for item in symbols:
    for dn in direction:
        symbol, lever_rate = item.values()
        subprocess.run(['pm2',
                        'start',
                        './martingale_usdt.py',
                        '--name',
                        symbol + '_' + dn + '_martingale',
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
                        '0.0,0.01,0.01,0.01,0.01',
                        '--close_call',
                        '0.05,0.04,0.03,0.02,0.01'])
