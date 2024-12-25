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
TARGET_GROUP = "linqingfeng221"
TOPIC_ID = 3
SESSIONS_DIR = "sessions"
MESSAGES_FILE = "话术/latest_messages.csv"

# 读取消息数据
df = pd.read_csv(MESSAGES_FILE)
messages = df.to_dict('records')

# 表情符号列表用于reactions
REACTION_EMOJIS = ['👍',  '🔥', '🎉', '🔥']

async def init_client(session_file):
    client = TelegramClient(os.path.join(SESSIONS_DIR, session_file.replace('.session', '')), 
                           API_ID, API_HASH)
    await client.start()
    return client

async def join_group(client):
    try:
        await client(JoinChannelRequest(TARGET_GROUP))
        print(f"Successfully joined {TARGET_GROUP}")
    except Exception as e:
        print(f"Error joining group: {e}")

async def get_recent_messages(client, limit=5):
    channel = await client.get_entity(TARGET_GROUP)
    messages = []
    async for message in client.iter_messages(channel, limit=limit, reply_to=TOPIC_ID):
        messages.append(message)
    return messages

async def process_action(client, message_data, recent_messages):
    try:
        channel = await client.get_entity(TARGET_GROUP)
        if recent_messages and random.random() < 0.2:
            target_message = recent_messages[-1]
            if random.random() < 0.5:
                emoji_reactions = ['👍', '🔥', '🎉', '💯']
                chosen_emoji = random.choice(emoji_reactions)
                reaction = [ReactionEmoji(emoticon=chosen_emoji)]
                reaction_text = '点赞' if chosen_emoji == '👍' else f'表情({chosen_emoji})'
                
                await client(SendReactionRequest(
                    peer=channel,
                    msg_id=target_message.id,
                    reaction=reaction
                ))
                me = await client.get_me()
                username = f"@{me.username}" if me.username else me.id
                print(f"{username} 对消息ID {target_message.id} 进行了{reaction_text}反应")
            else:
                await client.send_message(channel, message_data['message_content'], 
                                        reply_to=target_message.id)
        else:
            if message_data['message_type'] in ['video', 'photo']:
                media_path = message_data['media_path'].replace('话术\\', '')
                await client.send_file(channel, os.path.join("话术", media_path),
                                     reply_to=TOPIC_ID)
            else:
                await client.send_message(channel, message_data['message_content'],
                                        reply_to=TOPIC_ID)
    except Exception as e:
        print(f"Error processing action: {e}")

async def main():
    # 获取所有session文件
    session_files = [f for f in os.listdir(SESSIONS_DIR) if f.endswith('.session')]
    num_clients = len(session_files)
    
    # 初始化所有客户端
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
            await asyncio.sleep(random.uniform(1, 2))  # 1-2秒的随机延迟
    
    # 关闭所有客户端
    for client in clients:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())