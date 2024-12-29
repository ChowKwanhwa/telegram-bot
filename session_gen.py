#生成session文件，保存到sessions目录下

from telethon import TelegramClient
from telethon.sessions import StringSession
from dotenv import load_dotenv
import os

# 加载环境变量
load_dotenv()

# 从环境变量获取配置
api_id = int(os.getenv('API_ID'))
api_hash = os.getenv('API_HASH')

# 代理列表配置
PROXY_LIST = [
    {
        'proxy_type': 'socks5',
        'addr': '119.42.39.170',
        'port': 5798,
        'username': 'Maomaomao77',
        'password': 'Maomaomao77'
    },
    {
        'addr': "86.38.26.189",
        'port': 6354,
        'username': 'binghua99',
        'password': 'binghua99'
    },
    {
        'addr': "198.105.111.87",
        'port': 6765,
        'username': 'binghua99',
        'password': 'binghua99'
    },
    {
        'addr': "185.236.95.32",
        'port': 5993,
        'username': 'binghua99',
        'password': 'binghua99'
    }
]

async def try_connect_with_proxy(phone, sessions_dir, proxy_config):
    """尝试使用特定代理连接"""
    session_file = os.path.join(sessions_dir, f"{phone.replace('+', '')}.session")
    
    try:
        print(f"\n正在使用代理 {proxy_config['addr']}:{proxy_config['port']} 尝试连接...")
        client = TelegramClient(session_file, api_id, api_hash, proxy=proxy_config)
        
        # 启动客户端并等待验证码
        await client.connect()
        if not await client.is_user_authorized():
            print(f"\n正在发送验证码到 {phone}...")
            await client.send_code_request(phone)
            code = input(f"请输入发送到 {phone} 的验证码: ")
            await client.sign_in(phone, code)
        
        if await client.is_user_authorized():
            print(f"[成功] Session 文件已成功创建: {session_file}")
            me = await client.get_me()
            print(f"[成功] 已登录账号: {me.first_name} (@{me.username})")
            await client.disconnect()
            return True
            
    except Exception as e:
        print(f"[失败] 使用代理 {proxy_config['addr']} 时出错: {str(e)}")
        try:
            await client.disconnect()
        except:
            pass
    
    return False

async def process_phone(phone, sessions_dir):
    """处理单个电话号码，尝试所有代理"""
    for proxy in PROXY_LIST:
        success = await try_connect_with_proxy(phone, sessions_dir, proxy)
        if success:
            return True
    
    print(f"\n[失败] {phone} 所有代理均连接失败!")
    return False

async def main():
    # 创建 sessions 目录（如果不存在）
    sessions_dir = 'sessions'
    os.makedirs(sessions_dir, exist_ok=True)
    
    # 定义电话号码列表
    phone_numbers = [
        '+16157061556',  # 替换为实际的电话号码
        '+16157061573'
    ]
    
    # 批量处理每个电话号码
    for phone in phone_numbers:
        print(f"\n开始处理电话号码: {phone}")
        success = await process_phone(phone, sessions_dir)
        
        # 询问是否继续处理下一个号码
        if phone != phone_numbers[-1]:  # 如果不是最后一个号码
            continue_input = input("\n是否继续处理下一个号码？(y/n): ")
            if continue_input.lower() != 'y':
                print("停止处理剩余号码")
                break

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
    
