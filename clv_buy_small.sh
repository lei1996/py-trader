pm2 stop clv_buy_small
echo '' > ~/.pm2/logs/clv-buy-small-out.log
echo '' > ~/.pm2/logs/clv-buy-small-error.log
pm2 restart clv_buy_small