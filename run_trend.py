import subprocess

direction = ['buy', 'sell']
symbols = [{
    "symbol": 'doge',
    "lever_rate": '75'
}]

for item in symbols:
    for dn in direction:
        symbol, lever_rate = item.values()
        subprocess.run(['pm2',
                        'start',
                        './trend_usdt.py',
                        '--name',
                        symbol + '_' + dn + '_trend',
                        '--interpreter',
                        'python3',
                        '--',
                        '--symbol',
                        symbol.upper(),
                        '--max_cnt',
                        '6',
                        '--direction',
                        dn,
                        '--lever_rate',
                        lever_rate,
                        '--margin_call',
                        '0.0,0.01,0.01,0.01,0.01,0.01',
                        '--close_call',
                        '0.01,0.01,0.01,0.01,0.01,0.01'])
