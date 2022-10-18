pm2 stop xrp_buy_small
echo '' > ~/.pm2/logs/xrp-buy-small-out.log
echo '' > ~/.pm2/logs/xrp-buy-small-error.log
pm2 restart xrp_buy_small