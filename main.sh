pm2 stop main
echo '' > ~/.pm2/logs/main-out.log
echo '' > ~/.pm2/logs/main-error.log
pm2 restart main