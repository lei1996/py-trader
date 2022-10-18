pm2 stop ht_sell_small
echo '' > ~/.pm2/logs/ht-sell-small-out.log
echo '' > ~/.pm2/logs/ht-sell-small-error.log
pm2 restart ht_sell_small