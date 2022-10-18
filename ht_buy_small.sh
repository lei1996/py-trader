pm2 stop ht_buy_small
echo '' > ~/.pm2/logs/ht-buy-small-out.log
echo '' > ~/.pm2/logs/ht-buy-small-error.log
pm2 restart ht_buy_small