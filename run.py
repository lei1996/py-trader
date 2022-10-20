import subprocess

direction = ['buy', 'sell']
symbols = ['btc', 'eth']

for symbol in symbols:
    for dn in direction:
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
                        '--margin_call',
                        '0.0,0.0025,0.005,0.0075,0.01',
                        '--close_call',
                        '0.05,0.04,0.03,0.02,0.01'])
