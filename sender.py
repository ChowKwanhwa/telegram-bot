#如果是topic，使用flag --topic，并指定topic-id，如python sender.py --topic --topic-id 3

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
import argparse

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

def parse_args():
    parser = argparse.ArgumentParser(description='Telegram message sender')
    parser.add_argument('--topic', action='store_true', 
                       help='Enable topic mode for forum channels')
    parser.add_argument('--topic-id', type=int,
                       help=f'Topic ID for forum channels (default: {TOPIC_ID})')
    args = parser.parse_args()
    
    # 如果启用了topic模式但没有指定topic-id，使用默认的TOPIC_ID
    if args.topic and args.topic_id is None:
        args.topic_id = TOPIC_ID
        
    return args

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

async def get_recent_messages(client, limit=5, use_topic=False, topic_id=None):
    channel = await client.get_entity(TARGET_GROUP)
    messages = []
    kwargs = {}
    if use_topic:
        kwargs['reply_to'] = topic_id
    async for message in client.iter_messages(channel, limit=limit, **kwargs):
        messages.append(message)
    return messages[::-1]  # 反转消息列表，使最早的消���在前面

async def process_action(client, message_data, recent_messages, use_topic, topic_id):
    try:
        channel = await client.get_entity(TARGET_GROUP)
        
        # 在topic模式下添加对第五条消息的互动概率
        if use_topic and recent_messages and len(recent_messages) >= 5:
            random_value = random.random()
            if random_value < 0.3:  # 30%概率回复第五条消息
                target_message = recent_messages[4]  # 第五条消息
                kwargs = {'reply_to': target_message.id}
                await client.send_message(channel, message_data['message_content'], **kwargs)
                return
            elif random_value < 0.2:  # 20%概率对第五条消息添加表情反应
                target_message = recent_messages[4]  # 第五条消息
                chosen_emoji = random.choice(REACTION_EMOJIS)
                reaction = [ReactionEmoji(emoticon=chosen_emoji)]
                
                await client(SendReactionRequest(
                    peer=channel,
                    msg_id=target_message.id,
                    reaction=reaction
                ))
                me = await client.get_me()
                username = f"@{me.username}" if me.username else me.id
                print(f"{username} 对消息ID {target_message.id} 进行了表情({chosen_emoji})反应")
                return
        
        # 原有的处理逻辑
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
                kwargs = {'reply_to': target_message.id}
                if use_topic:
                    kwargs['reply_to'] = topic_id
                await client.send_message(channel, message_data['message_content'], **kwargs)
        else:
            kwargs = {}
            if use_topic:
                kwargs['reply_to'] = topic_id
                
            if message_data['message_type'] in ['video', 'photo']:
                media_path = message_data['media_path'].replace('话术\\', '')
                await client.send_file(channel, os.path.join("话术", media_path), **kwargs)
            else:
                await client.send_message(channel, message_data['message_content'], **kwargs)
    except Exception as e:
        print(f"Error processing action: {e}")

async def main():
    args = parse_args()
    topic_id = args.topic_id if args.topic else None
    print(f"Using topic mode: {args.topic}, topic ID: {topic_id}")  # 添加调试信息
    
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
        recent_messages = await get_recent_messages(clients[0], limit=5, 
                                                  use_topic=args.topic, 
                                                  topic_id=topic_id)
        
        batch_messages = messages[i:i + num_clients]
        if not batch_messages:
            break
            
        available_clients = clients.copy()
        random.shuffle(available_clients)
        
        for msg, client in zip(batch_messages, available_clients):
            await process_action(client, msg, recent_messages, args.topic, topic_id)
            await asyncio.sleep(random.uniform(1, 2))
    
    # 关闭所有客户端
    for client in clients:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())