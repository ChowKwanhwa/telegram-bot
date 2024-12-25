import os
import pandas as pd
from telethon import TelegramClient
import asyncio
import random
from telethon.tl.types import InputPeerChannel, ReactionEmoji
from telethon.tl.functions.messages import GetHistoryRequest, SendReactionRequest
import emoji
from dotenv import load_dotenv
from telethon.tl.functions.channels import JoinChannelRequest

# 加载.env文件
load_dotenv()

# 从环境变量获取API凭据
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")

# 其他配置
TARGET_GROUP = "https://t.me/linqingfeng221/3"
SESSIONS_DIR = "sessions"
MESSAGES_FILE = "话术/latest_messages.csv"

# 读取消息数据
df = pd.read_csv(MESSAGES_FILE)
messages = df.to_dict('records')

# 表情符号列表用于reactions
REACTION_EMOJIS = ['👍',  '🔥', '🎉', '🔥']

async def init_client(session_file):
    # 添加代理配置
    proxy = {
        'proxy_type': 'socks5',
        'addr': '132.148.167.243',
        'port': 40349,
    }   

    client = TelegramClient(os.path.join(SESSIONS_DIR, session_file.replace('.session', '')), 
                           API_ID, API_HASH, proxy=proxy)
    await client.start()
    return client

async def join_group(client):
    try:
        await client(JoinChannelRequest(TARGET_GROUP))
        print(f"Successfully joined {TARGET_GROUP}")
    except Exception as e:
        print(f"Error joining group: {e}")

async def get_recent_messages(client, limit=5):
    messages = []
    async for message in client.iter_messages(TARGET_GROUP, limit=limit):
        messages.append(message)
    return messages

async def process_action(client, message_data, recent_messages):
    try:
        if recent_messages and random.random() < 0.2:  # 50% chance for reaction/reply
            target_message = recent_messages[-1]
            if random.random() < 0.5:  # 50% chance for reaction
                # Simplified reaction handling
                emoji_reactions = ['👍', '🔥', '🎉', '💯']
                chosen_emoji = random.choice(emoji_reactions)
                reaction = [ReactionEmoji(emoticon=chosen_emoji)]
                reaction_text = '点赞' if chosen_emoji == '👍' else f'表情({chosen_emoji})'
                
                await client(SendReactionRequest(
                    peer=TARGET_GROUP,
                    msg_id=target_message.id,
                    reaction=reaction
                ))
                me = await client.get_me()
                username = f"@{me.username}" if me.username else me.id
                print(f"{username} 对消息ID {target_message.id} 进行了{reaction_text}反应")
            else:  # 50% chance for reply
                await client.send_message(TARGET_GROUP, message_data['message_content'], reply_to=target_message.id)
        else:  # 50% chance for original message
            if message_data['message_type'] == 'video':
                media_path = message_data['media_path'].replace('话术\\', '')
                await client.send_file(TARGET_GROUP, os.path.join("话术", media_path))
            elif message_data['message_type'] == 'photo':
                media_path = message_data['media_path'].replace('话术\\', '')
                await client.send_file(TARGET_GROUP, os.path.join("话术", media_path))
            else:
                await client.send_message(TARGET_GROUP, message_data['message_content'])
    except Exception as e:
        print(f"Error processing action: {e}")

async def main():
    # 获取所有session文件
    session_files = [f for f in os.listdir(SESSIONS_DIR) if f.endswith('.session')]
    num_clients = len(session_files)
    
    # 初始���所有客户端
    clients = []
    for session_file in session_files:
        client = await init_client(session_file)
        clients.append(client)
        await join_group(client)
    
    # 处理消息发送
    for i in range(0, len(messages), num_clients):
        # 获取最近的消息
        recent_messages = await get_recent_messages(clients[0], limit=5)
        
        # 获取下一批消息（批次大小等于客户端数量）
        batch_messages = messages[i:i + num_clients]
        if not batch_messages:
            break
            
        # 为这一批消息随机分配客户端
        available_clients = clients.copy()
        random.shuffle(available_clients)
        
        # 确保每个消息都有对应的客户端
        for msg, client in zip(batch_messages, available_clients):
            await process_action(client, msg, recent_messages)
            await asyncio.sleep(random.uniform(15, 20))  # 1-2秒的随机延迟
    
    # 关闭所有客户端
    for client in clients:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())