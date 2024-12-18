from tqsdk2 import TqApi, TqAuth
import pandas as pd
import time
import telegram
import asyncio
from functools import partial

# Telegram配置
TELEGRAM_BOT_TOKEN = '7173276947:AAEvtRbOH1DSM6t9aPUfmkjzYv-tXGbuaPA'  # 替换为你的bot token
TELEGRAM_CHAT_ID = '438441299'      # 替换为你的chat id

async def send_telegram_message(message):
    """发送Telegram消息"""
    bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)
    await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)

def check_ema_cross(api, symbol, kline_length=200):
    """
    检查指定合约的5分钟K线是否穿越EMA200
    返回: 1(上穿确认), -1(下穿确认), 2(可能上穿), -2(可能下穿), 0(无穿越)
    """
    klines = api.get_kline_serial(symbol, duration_seconds=5*60, data_length=300)
    df = pd.DataFrame(klines)
    
    # 计算EMA200
    df['ema200'] = df['close'].ewm(span=200, adjust=False).mean()
    
    # 获取最近的几根K线数据
    last_k = df.iloc[-1]    # 最新K线
    prev_k = df.iloc[-2]    # 前一根K线
    prev_prev_k = df.iloc[-3]  # 前两根K线
    
    # 判断穿越确认
    if prev_prev_k['close'] < prev_prev_k['ema200'] and prev_k['close'] > prev_k['ema200'] and last_k['close'] > last_k['ema200']:
        return 1, last_k['close'], last_k['ema200']  # 上穿确认
    elif prev_prev_k['close'] > prev_prev_k['ema200'] and prev_k['close'] < prev_k['ema200'] and last_k['close'] < last_k['ema200']:
        return -1, last_k['close'], last_k['ema200']  # 下穿确认
    # 判断可能穿越（需要下一根K线确认）
    elif prev_k['close'] < prev_k['ema200'] and last_k['close'] > last_k['ema200']:
        return 2, last_k['close'], last_k['ema200']  # 可能上穿
    elif prev_k['close'] > prev_k['ema200'] and last_k['close'] < last_k['ema200']:
        return -2, last_k['close'], last_k['ema200']  # 可能下穿
    
    return 0, last_k['close'], last_k['ema200']  # 无穿越

def monitor_contracts():
    """实时监控所有主力合约"""
    api = TqApi(auth=TqAuth("碗米林2022", "superlk321235"))
    
    # 用于记录已经输出过确认信号的合约
    confirmed_signals = {}
    
    # 创建异步事件循环
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        print("开始监控主力合约...")
        while True:
            main_contracts = api.query_quotes("KQ.m@")
            
            # 检查每个合约的EMA穿越情况
            for symbol in main_contracts:
                quote = api.get_quote(symbol)
                cross_type, current_price, ema_value = check_ema_cross(api, quote.underlying_symbol)
                
                # 只处理确认的穿越信号
                if abs(cross_type) == 1:  # 确认信号
                    status = "【确认】向上穿越" if cross_type == 1 else "【确认】向下穿越"
                    
                    # 如果该合约没有记录或者记录的信号类型不同，则输出并更新记录
                    if symbol not in confirmed_signals or confirmed_signals[symbol] != cross_type:
                        confirmed_signals[symbol] = cross_type
                        current_time = time.strftime("%Y-%m-%d %H:%M:%S")
                        
                        # 构建消息
                        message = (f"[{current_time}] 合约: {quote.underlying_symbol}\n"
                                 f"状态: {status}\n"
                                 f"当前价: {current_price:.2f}\n"
                                 f"EMA200: {ema_value:.2f}")
                        
                        # 打印到控制台
                        print(message)
                        
                        # 发送到Telegram
                        loop.run_until_complete(send_telegram_message(message))
            
            # 等待行情更新
            api.wait_update()
            
    except KeyboardInterrupt:
        print("\n监控已停止")
    finally:
        api.close()
        loop.close()

if __name__ == "__main__":
    monitor_contracts()