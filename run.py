import subprocess

# direction = ['buy', 'sell']
# symbols = ['btc', 'eth']

# for symbol in symbols:
#     for dn in direction:
#         subprocess.run(['pm2',
#                         'start',
#                         './martingale_usdt.py',
#                         '--name',
#                         symbol + '_' + dn,
#                         '--interpreter',
#                         'python3',
#                         '--',
#                         '--symbol',
#                         symbol.upper(),
#                         '--max_cnt',
#                         '5',
#                         '--direction',
#                         dn,
#                         '--margin_call',
#                         '0.0,0.0025,0.005,0.0075,0.01',
#                         '--close_call',
#                         '0.05,0.04,0.03,0.02,0.01'])

direction = ['buy', 'sell']
symbols = ['apt']

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
                        '10',
                        '--direction',
                        dn,
                        '--lever_rate',
                        '10',
                        '--margin_call',
                        '0.0,0.0056,0.012,0.0167,0.023,0.0278,0.034,0.039,0.046,0.05',
                        '--close_call',
                        '0.5,0.455,0.41,0.367,0.32,0.278,0.234,0.188,0.144,0.1'])
