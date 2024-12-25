from telethon import TelegramClient, events, functions
from datetime import datetime
import asyncio
import os
import logging
import csv
from dotenv import load_dotenv
import random

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

# 监控的群组列表
SOURCE_GROUPS = [
    '@MEXCEnglish',
    '@lipeixiamaoqi',
    '@CoinetOfficial',
    '@binanceexchange',
    '@bingxofficial',
    '@OKXOfficial_Customer'
]

# 创建保存目录
MONITORED_DIR = "monitoredMembers"
os.makedirs(MONITORED_DIR, exist_ok=True)

async def join_group(client, group):
    """检查并加入目标群组，返回 (成功与否, 是否新加入)"""
    try:
        # 获取群组实体
        entity = await client.get_entity(group)
        
        try:
            # 尝试获取自己的成员信息
            me = await client.get_me()
            await client.get_permissions(entity, me)
            logger.info(f"已经是群组成员: {group}")
            return True, False  # 成功，但不是新加入
            
        except Exception as e:
            if "USER_NOT_PARTICIPANT" in str(e):
                # 如果不是成员，尝试加入群组
                try:
                    await client(functions.channels.JoinChannelRequest(entity))
                    logger.info(f"成功加入群组: {group}")
                    return True, True  # 成功，且是新加入
                except Exception as join_error:
                    logger.error(f"加入群组失败 {group}: {str(join_error)}")
                    return False, False
            else:
                # 其他错误，也尝试加入群组
                try:
                    await client(functions.channels.JoinChannelRequest(entity))
                    logger.info(f"成功加入群组: {group}")
                    return True, True
                except Exception as join_error:
                    logger.error(f"加入群组失败 {group}: {str(join_error)}")
                    return False, False
                
    except Exception as e:
        logger.error(f"处理群组 {group} 时出错: {str(e)}")
        return False, False

async def save_user_data(user_data):
    """保存用户数据到CSV文件"""
    try:
        date_str = datetime.now().strftime('%Y%m%d')
        filename = os.path.join(MONITORED_DIR, f'active_users_{date_str}.csv')
        
        # 定义CSV表头
        fieldnames = ['timestamp', 'user_id', 'username', 'first_name', 'last_name', 'source_group', 'message']
        
        # 如果文件不存在，创建文件并写入表头
        file_exists = os.path.exists(filename)
        
        with open(filename, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            if not file_exists:
                writer.writeheader()
            
            # 写入数据
            writer.writerow({
                'timestamp': user_data['timestamp'],
                'user_id': user_data['user_id'],
                'username': user_data['username'],
                'first_name': user_data['first_name'],
                'last_name': user_data['last_name'],
                'source_group': user_data['source_group'],
                'message': user_data['message_text']
            })
            
        logger.info(f"已保存用户消息到 {filename}")
        
    except Exception as e:
        logger.error(f"保存数据失败: {e}")

async def main():
    # 获取第一个可用的 session 文件
    sessions_dir = "sessions"
    session_files = [f for f in os.listdir(sessions_dir) if f.endswith('.session')]
    
    if not session_files:
        logger.error("未找到任何 session 文件，请先运行 session_string.py 创建")
        return
        
    # 使用第一个 session 文件（不包含.session后缀）
    session_path = os.path.join(sessions_dir, session_files[0][:-8])
    logger.info(f"使用 session 文件: {session_files[0]}")
    
    client = TelegramClient(session_path, api_id, api_hash)
    
    try:
        await client.start()
        me = await client.get_me()
        logger.info(f"已登录账号: {me.first_name} (@{me.username})")

        # 依次检查和加入源群组
        logger.info("开始检查群组成员状态...")
        for group in SOURCE_GROUPS:
            success, is_new_join = await join_group(client, group)
            if success and is_new_join:
                # 只有新加入群组才等待
                wait_time = random.randint(10, 12)
                logger.info(f"等待 {wait_time} 秒后继续...")
                await asyncio.sleep(wait_time)
            elif not success:
                logger.warning(f"无法处理群组 {group}，但将继续处理其他群组")

        # 监听新消息
        @client.on(events.NewMessage(chats=SOURCE_GROUPS))
        async def message_handler(event):
            try:
                # 获取发送消息的用户
                sender = await event.get_sender()
                
                # 如果是机器人或没有username，则跳过
                if sender.bot or not sender.username:
                    return
                
                # 获取消息来源群组
                chat = await event.get_chat()
                source_group = f"@{chat.username}" if chat.username else 'Unknown'
                
                # 准备用户数据
                user_data = {
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'user_id': sender.id,
                    'username': sender.username,
                    'first_name': sender.first_name or '',
                    'last_name': sender.last_name or '',
                    'source_group': source_group,
                    'message_text': event.message.text.replace('\n', ' ')  # 替换换行符为空格
                }
                
                # 保存户数据
                await save_user_data(user_data)
                
            except Exception as e:
                logger.error(f"处理消息事件时出错: {str(e)}")
        
        # 保持程序运行
        logger.info("开始监控以下群组的消息:")
        for group in SOURCE_GROUPS:
            logger.info(f"- {group}")
            
        await client.run_until_disconnected()
        
    except Exception as e:
        logger.error(f"运行出错: {str(e)}")
    finally:
        await client.disconnect()

if __name__ == '__main__':
    asyncio.run(main())