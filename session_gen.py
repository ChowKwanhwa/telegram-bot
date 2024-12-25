from telethon import TelegramClient
from telethon.sessions import StringSession
from dotenv import load_dotenv
import os

# 加载环境变量
load_dotenv()

# 从环境变量获取配置
api_id = int(os.getenv('API_ID'))
api_hash = os.getenv('API_HASH')

async def main():
    # 创建 sessions 目录（如果不存在）
    sessions_dir = 'sessions'
    os.makedirs(sessions_dir, exist_ok=True)
    
    phone = input("请输入电话号码: ")
    
    # 添加代理配置
    proxy = {
        'proxy_type': 'socks5',
        'addr': '132.148.167.243',
        'port': 40349,  # 根据你的代理端口进行修改
    }
    
    session_file = os.path.join(sessions_dir, f"{phone.replace('+', '')}.session")
    
    try:
        # 添加代理配置到客户端
        client = TelegramClient(session_file, api_id, api_hash, proxy=proxy)
        await client.start(phone)
        
        if await client.is_user_authorized():
            print(f"Session 文件已成功创建: {session_file}")
            me = await client.get_me()
            print(f"已登录账号: {me.first_name} (@{me.username})")
    
    except Exception as e:
        print(f"连接错误: {str(e)}")
        print("请确保：")
        print("1. 你的网络连接正常")
        print("2. 代理服务器正在运行")
        print("3. API ID 和 API Hash 正确")
    
    finally:
        await client.disconnect()

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
    
