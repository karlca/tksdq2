# 引入TqSdk模块
from tqsdk2 import TqApi, TqAuth
# 创建api实例，设置web_gui=True生成图形化界面
api = TqApi(web_gui=True, auth=TqAuth("碗米林2022", "superlk321235"))
# 订阅 ni2010 合约的10秒线
klines = api.get_kline_serial("SHFE.ni2010", 10)
while True:
    # 通过wait_update刷新数据
    api.wait_update()