from telethon import TelegramClient, events, functions, types
import csv
from datetime import datetime
import asyncio
import os
from dotenv import load_dotenv
import emoji
from pathlib import Path
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',  # 简化日志格式
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('telegram_download.log')  # 同时保存到文件
    ]
)

# 关闭 telethon 的详细连接日志
logging.getLogger('telethon').setLevel(logging.WARNING)

# 加载.env文件
load_dotenv()

# 配置路径
SESSIONS_DIR = "sessions"
DATA_DIR = "话术"
CSV_FILE = os.path.join(DATA_DIR, 'latest_messages.csv')
MEDIA_FOLDER = os.path.join(DATA_DIR, 'media_files')

# 创建必要的文件夹
os.makedirs(SESSIONS_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(MEDIA_FOLDER, exist_ok=True)

# 从环境变量获取配置
api_id = int(os.getenv('API_ID'))
api_hash = os.getenv('API_HASH')

# 监控的群组列表
SOURCE_GROUPS = [
    '@LSMM8',
]

# CSV表头配置
CSV_HEADERS = ['timestamp', 'group_name', 'username', 'message_type', 'message_content', 'media_path']

def sanitize_filename(filename):
    """清理文件名，移除非法字符"""
    return "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_', '.')).strip()

async def download_media_file(message, group_name):
    """下载媒体文件"""
    try:
        if message.media:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            # 获取文件扩展名
            if isinstance(message.media, types.MessageMediaPhoto):
                ext = '.jpg'
            elif isinstance(message.media, types.MessageMediaDocument):
                ext = os.path.splitext(message.file.name)[1] if message.file.name else '.unknown'
            else:
                ext = '.unknown'
            
            # 创建群组子文件夹
            group_folder = os.path.join(MEDIA_FOLDER, sanitize_filename(group_name.replace('@', '')))
            os.makedirs(group_folder, exist_ok=True)
            
            # 构建文件名
            filename = f"{timestamp}_{sanitize_filename(message.sender.username)}{ext}"
            filepath = os.path.join(group_folder, filename)
            
            # 下载文件
            await message.download_media(filepath)
            return filepath
    except Exception as e:
        logging.error(f"下载媒体文件时出错: {str(e)}")
    return None

async def get_message_content(message):
    """获取消息内容和类型"""
    if message.media:
        if isinstance(message.media, types.MessageMediaPhoto):
            return 'photo', message.message or ''
        elif isinstance(message.media, types.MessageMediaDocument):
            if message.media.document.mime_type == 'video/mp4':
                return 'video', message.message or ''
            elif message.media.document.mime_type.startswith('image'):
                return 'image', message.message or ''
            elif 'tgsticker' in message.media.document.mime_type:
                return 'sticker', message.message or ''
            else:
                return 'document', message.message or ''
    elif message.message:
        if any(char in emoji.EMOJI_DATA for char in message.message):
            return 'emoji', message.message
        return 'text', message.message
    return 'unknown', ''

async def save_to_csv(data):
    """保存数据到CSV文件"""
    file_exists = os.path.exists(CSV_FILE)
    
    with open(CSV_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
        if not file_exists:
            writer.writeheader()
        writer.writerow(data)

async def process_messages(client, group):
    """处理群组消息"""
    try:
        entity = await client.get_entity(group)
        messages = await client.get_messages(entity, limit=1000)
        
        total_messages = len(messages)
        processed = 0
        media_count = 0
        
        print(f"\n开始处理群组: {group}")
        print(f"找到 {total_messages} 条消息")
        
        for message in messages:
            try:
                processed += 1
                
                # 跳过机器人消息
                if message.sender and getattr(message.sender, 'bot', False):
                    continue
                
                # 获取消息类型和内容
                message_type, message_content = await get_message_content(message)
                
                # 跳过 unknown 类型的消息
                if message_type == 'unknown':
                    continue
                
                # 下载媒体文件
                media_path = ''
                if message.media:
                    print(f"正在下载媒体文件 ({processed}/{total_messages})...", end='\r')
                    media_path = await download_media_file(message, group)
                    if media_path:
                        media_count += 1
                
                # 准备数据
                message_data = {
                    'timestamp': message.date.strftime('%Y-%m-%d %H:%M:%S'),
                    'group_name': group,
                    'username': message.sender.username if message.sender else '',
                    'message_type': message_type,
                    'message_content': message_content,
                    'media_path': media_path or ''
                }
                
                # 保存到CSV
                await save_to_csv(message_data)
                
            except Exception as e:
                logging.error(f"处理消息时出错: {str(e)}")
        
        print(f"\n群组 {group} 处理完成:")
        print(f"- 总消息数: {total_messages}")
        print(f"- 媒体文件: {media_count}")
                
    except Exception as e:
        logging.error(f"处理群组 {group} 时出错: {str(e)}")

async def join_groups(client, groups):
    """加入所有源群组"""
    for group in groups:
        try:
            print(f"正在加入群组: {group}")
            entity = await client.get_entity(group)
            await client(functions.channels.JoinChannelRequest(entity))
            print(f"✓ 成功加入群组: {group}")
        except Exception as e:
            print(f"✗ 加入群组 {group} 失败: {str(e)}")

async def main():
    # 获取第一个可用的 session 文件
    session_files = [f for f in os.listdir(SESSIONS_DIR) if f.endswith('.session')]
    
    if not session_files:
        logging.error("未找到任何 session 文件，请先创建 session")
        return
        
    # 使用第一个 session 文件（不包含.session后缀）
    session_path = os.path.join(SESSIONS_DIR, session_files[0][:-8])
    logging.info(f"使用 session 文件: {session_files[0]}")
    
    client = TelegramClient(session_path, api_id, api_hash)
    
    try:
        await client.start()
        me = await client.get_me()
        print(f"已登录账号: {me.first_name} (@{me.username})")
        
        # 先加入所有群组
        print("\n=== 加入群组 ===")
        await join_groups(client, SOURCE_GROUPS)
        
        start_time = datetime.now()
        
        # 处理每个群组的消息
        print("\n=== 开始获取消息 ===")
        for group in SOURCE_GROUPS:
            await process_messages(client, group)
            
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print("\n任务完成统计:")
        print(f"- 处理群组数: {len(SOURCE_GROUPS)}")
        print(f"- 总耗时: {duration:.1f} 秒")
        print(f"- CSV文件: {os.path.abspath(CSV_FILE)}")
        print(f"- 媒体文件夹: {os.path.abspath(MEDIA_FOLDER)}")
        
    except Exception as e:
        logging.error(f"运行出错: {str(e)}")
    finally:
        await client.disconnect()

if __name__ == '__main__':
    # 配置事件循环
    if os.name == 'nt':  # Windows
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    # 运行主程序
    asyncio.run(main())