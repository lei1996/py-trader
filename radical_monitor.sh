pm2 stop radical_monitor_hb
echo '' > ~/.pm2/logs/radical-monitor-hb-out.log
echo '' > ~/.pm2/logs/radical-monitor-hb-error.log
pm2 restart radical_monitor_hb --cron-restart=0 --restart-delay=10000
