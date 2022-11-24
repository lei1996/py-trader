
# run:
    pm2 start martingale_usdt.py --name ht_buy_small --interpreter python3 -- --symbol HT --max_cnt 10 --direction buy --margin_call "0.0, 0.005555555555555556, 0.011111111111111112, 0.016666666666666666, 0.022222222222222223, 0.02777777777777778, 0.03333333333333333, 0.03888888888888889, 0.044444444444444446, 0.05" --close_call "0.5, 0.45555555555555555, 0.4111111111111111, 0.3666666666666667, 0.3222222222222222, 0.2777777777777778, 0.23333333333333334, 0.18888888888888888, 0.14444444444444443, 0.1"


# 监控所有运行的品种，突然爆拉或者暴跌，直接停止脚本
pm2 start martingale_monitor.py --name martingale_monitor --interpreter python3


pm2 start trend_monitor.py --name trend_monitor --interpreter python3


pm2 start radical_monitor.py --name radical_monitor_hb --interpreter python3



pm2 需要通过 -- 作为分隔符 区别 程序内部的参数


# 正向马丁，最开始开1， 然后每上涨1% 加仓， 滚雪球，然后下跌0.5%，平仓

然后 run.py 要和 监控脚本合并成启动脚本。

还是用原有的模式操作
先计算列表  然后每5秒钟监控一次k线


radical 激进策略，找出市场change 最大的5个品种， 关闭其他未达标的品种
