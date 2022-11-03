pm2 stop radical_monitor
echo '' > ~/.pm2/logs/radical-monitor-out.log
echo '' > ~/.pm2/logs/radical-monitor-error.log
pm2 restart radical_monitor --cron-restart=0 --restart-delay=60000
