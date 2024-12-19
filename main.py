from tqsdk2 import TqApi, TqAuth
import pandas as pd
import time
import telegram
import asyncio
from functools import partial
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID,TQ_USERNAME,TQ_PASSWORD



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
    last_k = df.iloc[-1]        # 最新K线
    prev_k = df.iloc[-2]        # 前一根K线
    prev_prev_k = df.iloc[-3]   # 前两根K线
    prev_prev_prev_k = df.iloc[-4]  # 前三根K线
    
    # 判断穿越确认 (需要三根K线确认)
    if (prev_prev_prev_k['close'] < prev_prev_prev_k['ema200'] and  # 第一根在均线下方
        prev_prev_k['close'] > prev_prev_k['ema200'] and            # 第二根突破均线
        prev_k['close'] > prev_k['ema200'] and                      # 第三根确认
        last_k['close'] > last_k['ema200']):                        # 当前K线保持
        return 1, last_k['close'], last_k['ema200']  # 上穿确认
    
    elif (prev_prev_prev_k['close'] > prev_prev_prev_k['ema200'] and  # 第一根在均线上方
          prev_prev_k['close'] < prev_prev_k['ema200'] and            # 第二根突破均线
          prev_k['close'] < prev_k['ema200'] and                      # 第三根确认
          last_k['close'] < last_k['ema200']):                        # 当前K线保持
        return -1, last_k['close'], last_k['ema200']  # 下穿确认
    
    # 判断可能穿越（需要后续K线确认）
    elif prev_k['close'] < prev_k['ema200'] and last_k['close'] > last_k['ema200']:
        return 2, last_k['close'], last_k['ema200']  # 可能上穿
    elif prev_k['close'] > prev_k['ema200'] and last_k['close'] < last_k['ema200']:
        return -2, last_k['close'], last_k['ema200']  # 可能下穿
    
    return 0, last_k['close'], last_k['ema200']  # 无穿越

def monitor_contracts():
    """实时监控所有主力合约"""
    api = TqApi(auth=TqAuth(TQ_USERNAME, TQ_PASSWORD))
    
    confirmed_signals = {}
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        print("开始监控主力合约...")
        while True:
            main_contracts = api.query_quotes("KQ.m@")
            
            for symbol in main_contracts:
                quote = api.get_quote(symbol)
                cross_type, current_price, ema_value = check_ema_cross(api, quote.underlying_symbol)
                
                if abs(cross_type) == 1:
                    status = "【确认】向上穿越" if cross_type == 1 else "【确认】向下穿越"
                    
                    if symbol not in confirmed_signals or confirmed_signals[symbol] != cross_type:
                        confirmed_signals[symbol] = cross_type
                        current_time = time.strftime("%Y-%m-%d %H:%M:%S")
                        
                        contract_quote = api.get_quote(quote.underlying_symbol)
                        
                        message = (f"[{current_time}]\n"
                                 f"合约: {quote.underlying_symbol} ({contract_quote.instrument_name})\n"
                                 f"状态: {status}\n"
                                 f"当前价: {current_price:.2f}\n"
                                 f"EMA200: {ema_value:.2f}")
                        
                        print(message)
                        
                        # 发送到Telegram（带重试机制）
                        success = loop.run_until_complete(send_telegram_message(message))
                        if not success:
                            print("消息发送失败，仅在控制台显示")
            
            api.wait_update()
            
    except KeyboardInterrupt:
        print("\n监控已停止")
    finally:
        api.close()
        loop.close()

if __name__ == "__main__":
    monitor_contracts()