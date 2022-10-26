pm2 stop martingale_monitor
echo '' > ~/.pm2/logs/martingale-monitor-out.log
echo '' > ~/.pm2/logs/martingale-monitor-error.log
pm2 restart martingale_monitor --cron-restart=0 --restart-delay=60000