pm2 stop trend_monitor
echo '' > ~/.pm2/logs/trend-monitor-out.log
echo '' > ~/.pm2/logs/trend-monitor-error.log
pm2 restart trend_monitor --cron-restart=0 --restart-delay=60000