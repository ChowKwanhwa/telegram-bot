from telethon import TelegramClient, events, functions, types
import csv
from datetime import datetime
import asyncio
import os
import logging
from dotenv import load_dotenv
from telethon.tl.functions.channels import GetParticipantsRequest
from telethon.tl.types import ChannelParticipantsRecent

# 配置日志
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler('telegram_monitor.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 加载.env文件
load_dotenv()

# 从环境变量获取配置
api_id = int(os.getenv('API_ID'))
api_hash = os.getenv('API_HASH')

# 其他配置
SESSION_FILE = 'session.session'
SOURCE_GROUPS = [
    '@MEXCEnglish',
    '@lipeixiamaoqi',
    '@CoinetOfficial',
    '@MEXCENGLISHcommunity'
]  # 监控的群组列表
TARGET_GROUP = '@PeanutButter116'  # 添加用户的目标群组

# CSV 文件配置
CSV_FILE = 'new_users.csv'
CSV_HEADERS = ['timestamp', 'user_id', 'username', 'first_name', 'last_name', 'is_bot', 'source_group']

async def save_to_csv(user_data):
    """保存用户数据到CSV文件"""
    try:
        file_exists = os.path.exists(CSV_FILE)
        
        with open(CSV_FILE, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
            if not file_exists:
                writer.writeheader()
            writer.writerow(user_data)
        logger.info(f"已保存用户数据到 {CSV_FILE}")
    except Exception as e:
        logger.error(f"保存CSV失败: {e}")

async def join_group(client, group):
    """加入目标群组"""
    try:
        entity = await client.get_entity(group)
        await client(functions.channels.JoinChannelRequest(entity))
        logger.info(f"成功加入群组: {group}")
        return True
    except Exception as e:
        logger.error(f"加入群组失败 {group}: {str(e)}")
        return False

async def add_user_to_group(client, user, target_group):
    """将用户添加到目标群组"""
    try:
        target_entity = await client.get_entity(target_group)
        user_to_add = await client.get_entity(user.username or user.id)
        await client(functions.channels.InviteToChannelRequest(
            channel=target_entity,
            users=[user_to_add]
        ))
        logger.info(f"成功将用户 @{user.username} 添加到 {target_group}")
    except Exception as e:
        logger.error(f"添加用户到群组失败: {str(e)}")

async def main():
    client = TelegramClient(SESSION_FILE, api_id, api_hash)
    
    try:
        await client.start()
        me = await client.get_me()
        logger.info(f"已登录账号: {me.first_name} (@{me.username})")
        
        # 加入所有源群组和目标群组
        join_results = []
        for group in SOURCE_GROUPS:
            join_results.append(await join_group(client, group))
        
        if not all(join_results) or not await join_group(client, TARGET_GROUP):
            logger.warning("部分群组加入失败，但程序将继续运行...")

        logger.info(f"开始监控以下群组的新订阅者:")
        for group in SOURCE_GROUPS:
            logger.info(f"- {group}")
        
        # 大型群组特殊处理监听器
        @client.on(events.ChatAction())
        async def all_chat_action_handler(event):
            try:
                # 调试：打印所有聊天动作事件
                logger.info(f"捕获到聊天动作事件：群组={event.chat.username if event.chat else 'None'}, 事件类型={type(event)}")
                
                # 检查是否为新用户加入事件
                if not (event.user_joined or event.user_added):
                    return
                
                # 检查事件是否来自监控的群组
                source_group = f"@{event.chat.username}" if event.chat and event.chat.username else 'Unknown'
                if source_group not in SOURCE_GROUPS:
                    logger.info(f"忽略非监控群组的事件: {source_group}")
                    return
                
                # 获取新加入的用户
                user = await event.get_user()
                
                # 准备用户数据
                user_data = {
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'user_id': user.id,
                    'username': user.username or '',
                    'first_name': user.first_name or '',
                    'last_name': user.last_name or '',
                    'is_bot': user.bot,
                    'source_group': source_group
                }
                
                # 详细日志记录
                logger.info(f"新用户加入事件 {source_group}:")
                logger.info(f"事件类型: {'用户加入' if event.user_joined else '用户被添加'}")
                logger.info(f"群组ID: {event.chat.id}")
                logger.info(f"用户信息: ID={user.id}, 用户名=@{user.username}, 名字={user.first_name}, 姓氏={user.last_name}")
                
                # 保存到CSV
                await save_to_csv(user_data)
                
                # 将用户添加到目标群组
                await add_user_to_group(client, user, TARGET_GROUP)
                
            except Exception as e:
                logger.error(f"处理新用户事件时出错: {str(e)}")
        
        # 保持程序运行
        logger.info("开始监听新成员加入事件...")
        await client.run_until_disconnected()
        
    except Exception as e:
        logger.error(f"运行出错: {str(e)}")
    finally:
        await client.disconnect()

if __name__ == '__main__':
    asyncio.run(main())