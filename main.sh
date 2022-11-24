pm2 stop xrp_buy
echo '' > ~/.pm2/logs/xrp-buy-out.log
echo '' > ~/.pm2/logs/xrp-buy-error.log
pm2 restart xrp_buy