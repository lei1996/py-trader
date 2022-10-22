import subprocess

direction = ['buy', 'sell']
symbols = ['btc', 'eth', 'clv', 'dydx', 'ht', 'apt']


subprocess.run('rm -rf ~/.pm2/logs/*', shell=True)

for symbol in symbols:
    for dn in direction:
        subprocess.run(['pm2', 'restart', symbol + '_' + dn])
