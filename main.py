from tqsdk2 import TqApi, TqAuth
import pandas as pd
import time
import telegram
import asyncio
from functools import partial
from datetime import datetime
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, TQ_USERNAME, TQ_PASSWORD, EXCLUDED_CONTRACTS

async def send_telegram_message(message, max_retries=3):
    """
    发送Telegram消息，带重试机制
    """
    for attempt in range(max_retries):
        try:
            bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)
            await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
            return True
        except Exception as e:
            if attempt == max_retries - 1:  # 最后一次尝试
                print(f"Telegram发送失败 ({attempt + 1}/{max_retries}): {str(e)}")
                return False
            print(f"Telegram发送重试 ({attempt + 1}/{max_retries})")
            await asyncio.sleep(2)  # 等待2秒后重试

def is_market_closed():
    """检查是否是收盘时间（15:15）"""
    current_time = datetime.now().time()
    # 判断是否是 15:15
    return current_time.hour == 15 and current_time.minute == 15

def check_multi_ema_cross(api, symbol):
    """
    检查指定合约的5分钟K线是否同时穿越所有EMA均线
    返回: (方向, 当前价格, 是否全部穿越)
    方向: 1(上穿确认), -1(下穿确认), 0(无穿越)
    """
    klines = api.get_kline_serial(symbol, duration_seconds=5*60, data_length=300)
    df = pd.DataFrame(klines)
    
    # 定义要监控的EMA周期列表
    ema_periods = [5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 
                  55, 60, 65, 70, 75, 80, 85, 90, 95, 100]
    
    # 计算所有EMA
    for period in ema_periods:
        df[f'ema{period}'] = df['close'].ewm(span=period, adjust=False).mean()
    
    # 获取最近的几根K线数据
    last_k = df.iloc[-1]    # 最新K线
    prev_k = df.iloc[-2]    # 前一根K线
    prev_prev_k = df.iloc[-3]   # 前两根K线
    
    # 检查是否所有均线都被穿越并得到第二根K线确认
    up_cross_count = 0
    down_cross_count = 0
    
    for period in ema_periods:
        ema_col = f'ema{period}'
        # 向上穿越并得到确认
        if (prev_prev_k['close'] < prev_prev_k[ema_col] and  # 第一根K线在均线下方
            prev_k['close'] > prev_k[ema_col] and            # 第二根K线突破并确认
            last_k['close'] > last_k[ema_col]):             # 当前K线保持在上方
            up_cross_count += 1
        # 向下穿越并得到确认
        elif (prev_prev_k['close'] > prev_prev_k[ema_col] and  # 第一根K线在均线上方
              prev_k['close'] < prev_k[ema_col] and            # 第二根K线突破并确认
              last_k['close'] < last_k[ema_col]):             # 当前K线保持在下方
            down_cross_count += 1
    
    # 只有当所有均线都被穿越且得到确认时才返回信号
    if up_cross_count == len(ema_periods):
        return 1, last_k['close'], True
    elif down_cross_count == len(ema_periods):
        return -1, last_k['close'], True
    
    return 0, last_k['close'], False

def check_daily_ema_cross(api, symbol):
    """
    检查指定合约的日K线是否同时穿越所有EMA均线
    返回: (方向, 当前价格, 是否全部穿越)
    方向: 1(上穿确认), -1(下穿确认), 0(无穿越)
    """
    # 获取日K线数据，确保有足够的数据计算均线
    klines = api.get_kline_serial(symbol, duration_seconds=24*60*60, data_length=300)
    df = pd.DataFrame(klines)
    
    # 定义要监控的EMA周期列表
    ema_periods = [5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 
                  55, 60, 65, 70, 75, 80, 85, 90, 95, 100]
    
    # 计算所有EMA
    for period in ema_periods:
        df[f'ema{period}'] = df['close'].ewm(span=period, adjust=False).mean()
    
    # 获取最近的几根K线数据
    last_k = df.iloc[-1]    # 最新K线
    prev_k = df.iloc[-2]    # 前一根K线
    prev_prev_k = df.iloc[-3]   # 前两根K线
    
    # 检查是否所有均线都被穿越并得到确认
    up_cross_count = 0
    down_cross_count = 0
    
    for period in ema_periods:
        ema_col = f'ema{period}'
        # 向上穿越并得到确认
        if (prev_prev_k['close'] < prev_prev_k[ema_col] and  # 第一根K线在均线下方
            prev_k['close'] > prev_k[ema_col] and            # 第二根K线突破并确认
            last_k['close'] > last_k[ema_col]):             # 当前K线保持在上方
            up_cross_count += 1
        # 向下穿越并得到确认
        elif (prev_prev_k['close'] > prev_prev_k[ema_col] and  # 第一根K线在均线上方
              prev_k['close'] < prev_k[ema_col] and            # 第二根K线突破并确认
              last_k['close'] < last_k[ema_col]):             # 当前K线保持在下方
            down_cross_count += 1
    
    # 只有当所有均线都被穿越且得到确认时才返回信号
    if up_cross_count == len(ema_periods):
        return 1, last_k['close'], True
    elif down_cross_count == len(ema_periods):
        return -1, last_k['close'], True
    
    return 0, last_k['close'], False

def generate_daily_report(signals_count):
    """生成每日统计报告"""
    report = ""
    
    # 按品种整理统计
    for symbol, counts in signals_count.items():
        report += f"品种: {symbol}\n"
        report += f"上穿次数: {counts.get(1, 0)}\n"
        report += f"下穿次数: {counts.get(-1, 0)}\n"
        report += "-" * 20 + "\n"
    
    # 计算总计
    total_up = sum(counts.get(1, 0) for counts in signals_count.values())
    total_down = sum(counts.get(-1, 0) for counts in signals_count.values())
    
    report += "\n总计:\n"
    report += f"总上穿次数: {total_up}\n"
    report += f"总下穿次数: {total_down}\n"
    
    return report

def monitor_contracts():
    """实时监控所有主力合约"""
    api = TqApi(auth=TqAuth(TQ_USERNAME, TQ_PASSWORD))
    
    alerted_crosses = {}  # 格式: {symbol: (5min_direction, daily_direction)}
    signals_count = {}  # 用于记录每个品种的穿越次数
    last_report_time = None
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        print("开始监控主力合约...")
        print(f"已排除以下合约: {', '.join(EXCLUDED_CONTRACTS)}")
        
        while True:
            current_time = datetime.now()
            
            # 检查是否需要发送日报
            if (is_market_closed() and 
                (last_report_time is None or 
                 current_time.date() != last_report_time.date())):
                if signals_count:
                    report = f"=== {current_time.strftime('%Y-%m-%d')} 交易日统计报告 ===\n\n"
                    report += generate_daily_report(signals_count)
                    print(report)
                    loop.run_until_complete(send_telegram_message(report))
                    signals_count = {}
                    alerted_crosses = {}
                last_report_time = current_time
            
            main_contracts = api.query_quotes("KQ.m@")
            
            for symbol in main_contracts:
                # 检查是否在排除列表中
                if any(excluded in symbol for excluded in EXCLUDED_CONTRACTS):
                    continue
                    
                quote = api.get_quote(symbol)
                
                # 检查5分钟K线穿越
                min5_cross, min5_price, min5_all_crossed = check_multi_ema_cross(api, quote.underlying_symbol)
                # 检查日线穿越
                daily_cross, daily_price, daily_all_crossed = check_daily_ema_cross(api, quote.underlying_symbol)
                
                # 初始化该合约的记录
                if quote.underlying_symbol not in alerted_crosses:
                    alerted_crosses[quote.underlying_symbol] = {'5min': 0, 'daily': 0}
                
                # 处理5分钟信号
                if (min5_cross != 0 and min5_all_crossed and 
                    alerted_crosses[quote.underlying_symbol]['5min'] != min5_cross):
                    
                    status = "【5分钟同时上穿所有均线】" if min5_cross == 1 else "【5分钟同时下穿所有均线】"
                    alerted_crosses[quote.underlying_symbol]['5min'] = min5_cross
                    
                    if quote.underlying_symbol not in signals_count:
                        signals_count[quote.underlying_symbol] = {1: 0, -1: 0}
                    signals_count[quote.underlying_symbol][min5_cross] += 1
                    
                    message = (f"[{time.strftime('%Y-%m-%d %H:%M:%S')}]\n"
                             f"合约: {quote.underlying_symbol} ({quote.instrument_name})\n"
                             f"状态: {status}\n"
                             f"当前价: {min5_price:.2f}")
                    
                    print(message)
                    loop.run_until_complete(send_telegram_message(message))
                
                # 处理日线信号
                if (daily_cross != 0 and daily_all_crossed and 
                    alerted_crosses[quote.underlying_symbol]['daily'] != daily_cross):
                    
                    status = "【日线同时上穿所有均线】" if daily_cross == 1 else "【日线同时下穿所有均线】"
                    alerted_crosses[quote.underlying_symbol]['daily'] = daily_cross
                    
                    message = (f"[{time.strftime('%Y-%m-%d %H:%M:%S')}]\n"
                             f"合约: {quote.underlying_symbol} ({quote.instrument_name})\n"
                             f"状态: {status}\n"
                             f"当前价: {daily_price:.2f}")
                    
                    print(message)
                    loop.run_until_complete(send_telegram_message(message))
            
            api.wait_update()
            
    except KeyboardInterrupt:
        print("\n监控已停止")
    finally:
        if signals_count:
            report = f"=== {current_time.strftime('%Y-%m-%d')} 最终统计报告 ===\n\n"
            report += generate_daily_report(signals_count)
            print(report)
            loop.run_until_complete(send_telegram_message(report))
        api.close()
        loop.close()

if __name__ == "__main__":
    monitor_contracts()