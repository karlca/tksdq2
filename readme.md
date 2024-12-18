# 期货主力合约EMA监控系统

这是一个基于天勤量化交易平台(TqSdk2)的期货主力合约监控系统，可以实时监控所有期货主力合约的EMA200均线穿越情况，并通过Telegram机器人发送提醒。

## 功能特点

- 实时监控所有期货主力合约
- 自动计算5分钟K线的EMA200均线
- 检测价格对EMA200的穿越情况
- 支持以下穿越信号：
  - 向上穿越确认
  - 向下穿越确认
  - 可能向上穿越（待确认）
  - 可能向下穿越（待确认）
- 通过Telegram机器人实时推送提醒消息
- 在控制台同步显示监控信息

## 安装步骤

1. 克隆项目到本地：
```bash
git clone [项目地址]
cd [项目目录]
```

2. 安装依赖包：
```bash
pip install tqsdk2 pandas python-telegram-bot
```

3. 创建配置文件 `config.py`，填入以下内容：
```python
# Telegram配置
TELEGRAM_BOT_TOKEN = "你的Telegram机器人Token"
TELEGRAM_CHAT_ID = "你的Telegram聊天ID"

# 天勤账号配置
TQ_USERNAME = "你的天勤账号"
TQ_PASSWORD = "你的天勤密码"
```

## 使用说明

1. 确保已正确配置 `config.py` 文件
2. 运行主程序：
```bash
python main.py
```

3. 程序会在控制台显示监控开始信息，并在检测到穿越信号时：
   - 在控制台打印详细信息
   - 通过Telegram发送通知消息

## 监控信息格式

每条监控信息包含以下内容：
- 时间戳
- 合约代码和名称
- 穿越状态（向上/向下）
- 当前价格
- EMA200数值

示例：
```
[2024-01-20 14:30:00]
合约: SHFE.cu2402 (沪铜2402)
状态: 【确认】向上穿越
当前价: 69290.00
EMA200: 69280.00
```

## 注意事项

1. 需要有效的天勤量化账号
2. 需要自行创建Telegram机器人并获取Token
3. 确保网络连接稳定
4. 建议在服务器上长期运行以获得持续监控

## 错误处理

如果遇到以下情况：
1. 网络连接中断：程序会自动重试连接
2. 天勤账号验证失败：检查账号密码是否正确
3. Telegram发送失败：检查Token和网络连接

## 贡献指南

欢迎提交Issue和Pull Request来改进这个项目。

## 许可证

MIT License
