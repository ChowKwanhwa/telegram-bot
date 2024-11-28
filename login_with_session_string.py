from telethon import TelegramClient, functions, types
from telethon.sessions import StringSession
import asyncio
from dotenv import load_dotenv
import os
# 加载.env文件
load_dotenv()

# 从环境变量获取配置
api_id = int(os.getenv('API_ID'))
api_hash = os.getenv('API_HASH')
TARGET_USERNAME = '@lipeixiamaoqi'  # 目标用户名

# Session string
SESSION = os.getenv('SESSION_STRING')

# 要发送的消息列表
messages = [
    "Hello! I just joined this group!",
    "这是自动发送的消息",
    "测试消息3"
]

async def join_chat(client, username):
    """尝试加入群组"""
    try:
        # 获取群组/频道信息
        entity = await client.get_entity(username)
        
        # 尝试加入
        await client(functions.channels.JoinChannelRequest(entity))
        print(f"成功加入: {username}")
        return True
    except Exception as e:
        print(f"加入群组失败: {str(e)}")
        return False

async def main():
    # 使用session string创建客户端
    async with TelegramClient(StringSession(SESSION), api_id, api_hash) as client:
        try:
            # 验证登录状态
            me = await client.get_me()
            print(f"已登录账号: {me.first_name} (@{me.username})")
            
            # 尝试加入群组
            if await join_chat(client, TARGET_USERNAME):
                print("等待5秒后开始发送消息...")
                await asyncio.sleep(5)  # 加入后等待一下再发送消息
                
                # 发送消息
                for message in messages:
                    try:
                        await client.send_message(TARGET_USERNAME, message)
                        print(f"成功发送消息: {message}")
                        # 消息发送间隔2秒
                        await asyncio.sleep(2)
                    except Exception as e:
                        print(f"发送消息失败: {str(e)}")
            else:
                print("由于无法加入群组，消息发送取消")
                    
        except Exception as e:
            print(f"运行出错: {str(e)}")

if __name__ == '__main__':
    asyncio.run(main())
