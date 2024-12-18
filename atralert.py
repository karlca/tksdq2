import pandas as pd
import numpy as np

def calculate_supertrend(df, period=10, multiplier=3.0):
    """
    计算 SuperTrend 指标
    
    参数:
        df: DataFrame, 必须包含 high, low, close 列
        period: ATR周期
        multiplier: ATR乘数
    
    返回:
        包含 supertrend 和信号的 DataFrame
    """
    
    # 计算 ATR
    df['tr'] = np.maximum(
        np.maximum(
            df['high'] - df['low'],
            abs(df['high'] - df['close'].shift(1))
        ),
        abs(df['low'] - df['close'].shift(1))
    )
    df['atr'] = df['tr'].rolling(period).mean()
    
    # 计算基础上轨和下轨
    hl2 = (df['high'] + df['low']) / 2
    df['up_basic'] = hl2 - (multiplier * df['atr'])
    df['down_basic'] = hl2 + (multiplier * df['atr'])
    
    # 计算最终上轨和下轨
    df['up'] = df['up_basic']
    df['down'] = df['down_basic']
    
    # 初始化趋势
    df['trend'] = 0
    df['supertrend'] = 0
    
    # 第一个值的趋势初始化
    if df.iloc[0]['close'] > df.iloc[0]['down_basic']:
        df.iloc[0, df.columns.get_loc('trend')] = 1
    else:
        df.iloc[0, df.columns.get_loc('trend')] = -1
        
    # 计算超级趋势
    for i in range(1, len(df)):
        curr = df.iloc[i]
        prev = df.iloc[i-1]
        
        # 上轨计算
        if curr['up_basic'] > prev['up'] or prev['close'] < prev['up']:
            df.iloc[i, df.columns.get_loc('up')] = curr['up_basic']
        else:
            df.iloc[i, df.columns.get_loc('up')] = prev['up']
            
        # 下轨计算
        if curr['down_basic'] < prev['down'] or prev['close'] > prev['down']:
            df.iloc[i, df.columns.get_loc('down')] = curr['down_basic']
        else:
            df.iloc[i, df.columns.get_loc('down')] = prev['down']
            
        # 趋势判断
        if curr['close'] > prev['down']:
            df.iloc[i, df.columns.get_loc('trend')] = 1
        elif curr['close'] < prev['up']:
            df.iloc[i, df.columns.get_loc('trend')] = -1
        else:
            df.iloc[i, df.columns.get_loc('trend')] = prev['trend']
            
        # 设置超级趋势值
        if df.iloc[i]['trend'] == 1:
            df.iloc[i, df.columns.get_loc('supertrend')] = df.iloc[i]['up']
        else:
            df.iloc[i, df.columns.get_loc('supertrend')] = df.iloc[i]['down']
    
    # 计算买卖信号
    df['buy_signal'] = (df['trend'] == 1) & (df['trend'].shift(1) == -1)
    df['sell_signal'] = (df['trend'] == -1) & (df['trend'].shift(1) == 1)
    
    return df

def check_supertrend_signals(df):
    """
    检查最新的SuperTrend信号
    
    返回:
        1: 买入信号
        -1: 卖出信号
        0: 无信号
    """
    if df['buy_signal'].iloc[-1]:
        return 1
    elif df['sell_signal'].iloc[-1]:
        return -1
    return 0
