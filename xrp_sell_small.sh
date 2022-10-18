pm2 stop xrp_sell_small
echo '' > ~/.pm2/logs/xrp-sell-small-out.log
echo '' > ~/.pm2/logs/xrp-sell-small-error.log
pm2 restart xrp_sell_small