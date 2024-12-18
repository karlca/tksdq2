from tqsdk2 import TqApi, TqAuth

def get_main_contracts():
    """获取所有期货主力合约"""
    # 创建API实例
    api = TqApi(auth=TqAuth("碗米林2022", "superlk321235"))
    
    try:
        # 获取所有以 KQ.m 开头的合约
        main_contracts = api.query_quotes("KQ.m@")
        print(f"\n获取到 {len(main_contracts)} 个主力合约")
        
        # 打印所有获取到的主力合约信息
        for symbol in main_contracts:
            quote = api.get_quote(symbol)
            print(f"主力合约代码: {symbol}, 对应实际合约: {quote.underlying_symbol}, 最新价: {quote.last_price}")
        
        return main_contracts
        
    finally:
        # 关闭API连接
        api.close()

if __name__ == "__main__":
    main_contracts = get_main_contracts()