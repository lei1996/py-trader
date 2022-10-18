pm2 stop clv_sell_small
echo '' > ~/.pm2/logs/clv-sell-small-out.log
echo '' > ~/.pm2/logs/clv-sell-small-error.log
pm2 restart clv_sell_small