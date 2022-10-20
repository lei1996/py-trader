import subprocess

direction = ['buy', 'sell']
# symbols = ['btc', 'eth', 'clv', 'dydx', 'ht']
symbols = ['dydx', 'ht']
# symbols = ['clv']

for symbol in symbols:
    for dn in direction:
        # subprocess.run(['pm2', 'stop', symbol + '_' + dn])
        subprocess.run(['pm2', 'stop', symbol + '_' + dn + '_small'])
        subprocess.run('rm -rf ~/.pm2/logs/'+ symbol + '-' + dn + '*', shell=True)
        # subprocess.run(['pm2', 'restart', symbol + '_' + dn])
        subprocess.run(['pm2', 'restart', symbol + '_' + dn + '_small'])
