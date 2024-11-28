from telethon import TelegramClient, events, functions
import csv
from datetime import datetime
import asyncio
import os
from dotenv import load_dotenv
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)

# 加载.env文件
load_dotenv()

# 从环境变量获取配置
api_id = int(os.getenv('API_ID'))
api_hash = os.getenv('API_HASH')

# 配置
SESSION_FILE = 'session.session'
SOURCE_GROUPS = [
    '@MEXCEnglish',
    '@lipeixiamaoqi',
    '@CoinetOfficial',
    '@MEXCENGLISHcommunity'
]

# CSV 文件配置
CSV_FILE = 'active_users.csv'
CSV_HEADERS = ['timestamp', 'group_name', 'username', 'message_text']

async def save_to_csv(data):
    """保存数据到CSV文件"""
    file_exists = os.path.exists(CSV_FILE)
    
    with open(CSV_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
        if not file_exists:
            writer.writeheader()
        writer.writerow(data)

async def join_group(client, group):
    """加入目标群组"""
    try:
        entity = await client.get_entity(group)
        await client(functions.channels.JoinChannelRequest(entity))
        print(f"成功加入群组: {group}")
        return True
    except Exception as e:
        print(f"加入群组失败 {group}: {str(e)}")
        return False

async def main():
    client = TelegramClient(
        SESSION_FILE, 
        api_id, 
        api_hash,
        connection_retries=None,
        retry_delay=1,
        auto_reconnect=True,
        request_retries=5
    )
    
    try:
        await client.start()
        me = await client.get_me()
        print(f"已登录账号: {me.first_name} (@{me.username})")
        
        # 并行加入群组
        join_tasks = [join_group(client, group) for group in SOURCE_GROUPS]
        await asyncio.gather(*join_tasks)
        
        # 监控新消息
        @client.on(events.NewMessage(chats=SOURCE_GROUPS))
        async def handler(event):
            try:
                # 异步获取发送者信息
                sender, group_entity = await asyncio.gather(
                    event.get_sender(),
                    event.get_chat()
                )
                
                # 检查是否是机器人或没有username
                if sender.bot or not sender.username:
                    return
                    
                group_name = f"@{group_entity.username}"
                message_text = event.message.text if event.message.text else ""
                
                # 准备数据
                user_data = {
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'group_name': group_name,
                    'username': sender.username,
                    'message_text': message_text
                }
                
                # 异步打印和保存
                print(f"\n新消息 from {group_name}:")
                print(f"用户: @{sender.username}")
                print(f"消息: {message_text[:100]}...")  # 只打印前100个字符
                
                # 异步保存
                asyncio.create_task(save_to_csv(user_data))
                
            except Exception as e:
                print(f"处理新消息时出错: {str(e)}")
        
        print("\n开始监控群组的新消息...")
        print("监控的群组:")
        for group in SOURCE_GROUPS:
            print(f"- {group}")
            
        # 保持连接活跃
        async def keep_alive():
            while True:
                try:
                    await client.get_me()
                    await asyncio.sleep(60)
                except Exception as e:
                    print(f"保持连接时出错: {str(e)}")
                    await asyncio.sleep(5)
        
        # 并行运行
        await asyncio.gather(
            keep_alive(),
            client.run_until_disconnected()
        )
        
    except Exception as e:
        print(f"运行出错: {str(e)}")
    finally:
        await client.disconnect()

if __name__ == '__main__':
    # 配置事件循环
    if os.name == 'nt':  # Windows
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    # 运行主程序
    asyncio.run(main()) 