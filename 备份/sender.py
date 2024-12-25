import os
import asyncio
import logging
import pandas as pd
from telethon import TelegramClient
from datetime import datetime
import random
import time
from dotenv import load_dotenv
import sys
from telethon.tl.types import MessageMediaDocument, MessageMediaPhoto
import tempfile
import subprocess
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import ImportChatInviteRequest
from telethon.errors import (
    ChannelPrivateError,
    InviteHashInvalidError,
    UserAlreadyParticipantError,
    FloodWaitError
)

# 加载.env文件
load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('auto_send.log'),
        logging.StreamHandler()
    ]
)

# 从环境变量获取配置
API_ID = int(os.getenv('API_ID'))
API_HASH = os.getenv('API_HASH')
SESSIONS_DIR = "sessions"
MESSAGES_FILE = "话术/latest_messages.csv"
MEDIA_DIR = "话术/media_files"
TARGET_GROUPS = ['@fsfwettwg']

async def load_messages():
    """加载消息数据"""
    try:
        df = pd.read_csv(MESSAGES_FILE)
        messages = []
        for _, row in df.iterrows():
            msg = {
                'type': row['message_type'],
                'content': row['message_content'],
                'media_path': row['media_path'] if pd.notna(row['media_path']) else None
            }
            messages.append(msg)
        logging.info(f"成功加载 {len(messages)} 条消息")
        return messages
    except Exception as e:
        logging.error(f"加载消息失败: {str(e)}")
        return []

async def convert_webm_to_mp4(webm_path):
    """将webm文件转换为mp4格式"""
    try:
        # 创建临时文件
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp_file:
            mp4_path = tmp_file.name
            
        # 使用 ffmpeg 命令行转换
        command = [
            'ffmpeg',
            '-i', webm_path,
            '-c:v', 'libx264',
            '-c:a', 'aac',
            '-y',  # 覆盖输出文件
            mp4_path
        ]
        
        # 执行转换
        process = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        if process.returncode == 0:
            logging.info(f"视频转换成功: {webm_path} -> {mp4_path}")
            return mp4_path
        else:
            logging.error(f"视频转换失败: {process.stderr}")
            if os.path.exists(mp4_path):
                os.remove(mp4_path)
            return None
            
    except Exception as e:
        logging.error(f"视频转换失败: {str(e)}")
        if 'mp4_path' in locals() and os.path.exists(mp4_path):
            os.remove(mp4_path)
        return None

async def send_message(client, chat_id, message):
    """发送单条消息"""
    try:
        me = await client.get_me()
        username = f"@{me.username}" if me.username else me.id
        
        if message['type'] == 'text':
            await client.send_message(chat_id, message['content'])
            logging.info(f"{username} 发送文本消息: {message['content'][:30]}...")
            
        elif message['type'] in ['video', 'document']:
            if message['media_path'] and os.path.exists(message['media_path']):
                file_path = message['media_path']
                # 如果是webm文件，先转换为mp4
                if file_path.lower().endswith('.webm'):
                    logging.info(f"正在转换webm文件: {file_path}")
                    mp4_path = await convert_webm_to_mp4(file_path)
                    if mp4_path:
                        try:
                            await client.send_file(
                                chat_id,
                                mp4_path,
                                force_document=False,
                                supports_streaming=True
                            )
                            logging.info(f"{username} 发送转换后的视频: {os.path.basename(file_path)}")
                        finally:
                            # 确保无论发送成功与否都删除临时文件
                            if os.path.exists(mp4_path):
                                os.remove(mp4_path)
                    else:
                        logging.error(f"无法转换文件: {file_path}")
                        return False
                else:
                    await client.send_file(chat_id, file_path)
                    logging.info(f"{username} 发送文件: {os.path.basename(file_path)}")
            else:
                logging.error(f"文件不存在: {message['media_path']}")
                return False
                    
        elif message['type'] in ['image', 'sticker', 'emoji']:
            if message['media_path'] and os.path.exists(message['media_path']):
                await client.send_file(chat_id, message['media_path'])
                logging.info(f"{username} 发送媒体: {os.path.basename(message['media_path'])}")
            elif message['type'] == 'emoji':
                await client.send_message(chat_id, message['content'])
                logging.info(f"{username} 发送表情")
            else:
                logging.error(f"文件不存在: {message['media_path']}")
                return False
        
        # 随机等待2-3秒
        await asyncio.sleep(random.uniform(2, 3))
        return True
        
    except Exception as e:
        logging.error(f"发送消息失败 ({username}): {str(e)}")
        return False

async def download_media_from_group(client, group_id):
    """从群组下载媒体文件"""
    try:
        logging.info(f"开始从 {group_id} 下载媒体文件...")
        
        # 创建media_files目录
        os.makedirs(os.path.join("话术", "media_files", "CoinetOfficial"), exist_ok=True)
        
        # 获取最近的消息
        async for message in client.iter_messages(group_id, limit=100):  # 可以调整limit
            if message.media:
                # 获取文件名
                if message.file:
                    original_filename = message.file.name or f"{message.date.strftime('%Y%m%d_%H%M%S')}_{message.sender_id}"
                    
                    # 根据媒体类型设置扩展名
                    if isinstance(message.media, MessageMediaDocument):
                        ext = os.path.splitext(original_filename)[1] or '.mp4'  # 默认扩展名
                    elif isinstance(message.media, MessageMediaPhoto):
                        ext = '.jpg'
                    else:
                        ext = os.path.splitext(original_filename)[1] or ''
                    
                    # 构建保存路径
                    filename = f"{message.date.strftime('%Y%m%d_%H%M%S')}_{message.sender.username or message.sender_id}{ext}"
                    save_path = os.path.join("话术", "media_files", "CoinetOfficial", filename)
                    
                    # 如果文件不存在，则下载
                    if not os.path.exists(save_path):
                        await message.download_media(save_path)
                        logging.info(f"已下载: {filename}")
                        await asyncio.sleep(0.5)  # 添加短暂延迟，避免过快下载
        
        logging.info("媒体文件下载完成")
        
    except Exception as e:
        logging.error(f"下载媒体文件时出错: {str(e)}")

async def ensure_group_membership(client, group):
    """确保账号已加入群组"""
    try:
        me = await client.get_me()
        username = f"@{me.username}" if me.username else me.id
        
        try:
            # 检查是否已经是群组成员
            entity = await client.get_entity(group)
            participants = await client.get_participants(entity, limit=1)
            logging.info(f"账号 {username} 已经是群组 {group} 的成员")
            return True
            
        except ChannelPrivateError:
            # 如果是私有群组，尝试加入
            if group.startswith('@'):
                # 公开群组
                try:
                    await client(JoinChannelRequest(group))
                    logging.info(f"账号 {username} 成功加入群组 {group}")
                    # 加入后等待5-10秒
                    await asyncio.sleep(random.uniform(5, 10))
                    return True
                except Exception as e:
                    logging.error(f"账号 {username} 加入群组 {group} 失败: {str(e)}")
                    return False
            else:
                # 私有群组（通过邀请链接）
                try:
                    hash = group.split('/')[-1]
                    await client(ImportChatInviteRequest(hash))
                    logging.info(f"账号 {username} 成功加入私有群组")
                    # 加入后等待5-10秒
                    await asyncio.sleep(random.uniform(5, 10))
                    return True
                except UserAlreadyParticipantError:
                    logging.info(f"账号 {username} 已经是群组成员")
                    return True
                except InviteHashInvalidError:
                    logging.error(f"群组 {group} 的邀请链接无效")
                    return False
                except FloodWaitError as e:
                    logging.error(f"账号 {username} 需要等待 {e.seconds} 秒后才能加入群组")
                    return False
                except Exception as e:
                    logging.error(f"账号 {username} 加入私有群组失败: {str(e)}")
                    return False
                    
    except Exception as e:
        logging.error(f"检查群组成员状态失败: {str(e)}")
        return False

async def main():
    # 获取所有session文件
    session_files = [f for f in os.listdir(SESSIONS_DIR) if f.endswith('.session')]
    if not session_files:
        logging.error("未找到任何session文件")
        return
        
    logging.info(f"找到 {len(session_files)} 个session文件")
    
    # 创建客户端列表
    clients = []
    for session_file in session_files:
        session_path = os.path.join(SESSIONS_DIR, session_file[:-8])
        client = TelegramClient(session_path, API_ID, API_HASH)
        clients.append(client)
    
    # 连接所有客户端并确保加入群组
    for client in clients:
        try:
            await client.start()
            me = await client.get_me()
            username = f"@{me.username}" if me.username else me.id
            logging.info(f"已登录账号: {me.first_name} ({username})")
            
            # 确保加入所有目标群组
            for group in TARGET_GROUPS:
                if not await ensure_group_membership(client, group):
                    logging.error(f"账号 {username} 无法加入群组 {group}，跳过该账号")
                    await client.disconnect()
                    clients.remove(client)
                    break
                
        except Exception as e:
            logging.error(f"客户端连接或加入群组失败: {str(e)}")
            clients.remove(client)
            continue
    
    if not clients:
        logging.error("没有可用的客户端，程序退出")
        return
        
    # 使用第一个可用客户端下载媒体文件
    try:
        me = await clients[0].get_me()
        logging.info(f"使用账号 {me.username} 下载媒体文件")
        
        for group in TARGET_GROUPS:
            await download_media_from_group(clients[0], group)
            
    except Exception as e:
        logging.error(f"下载媒体文件失败: {str(e)}")
        return

    # 重新加载消息
    messages = await load_messages()
    if not messages:
        return
        
    # 连接所有客户端
    for client in clients:
        try:
            await client.start()
            me = await client.get_me()
            logging.info(f"已登录账号: {me.first_name} (@{me.username})")
        except Exception as e:
            logging.error(f"客户端连接失败: {str(e)}")
            return
    
    try:
        # 循环发送消息
        current_client_index = 0
        
        while True:
            for message in messages:
                # 轮流使用不同账号
                client = clients[current_client_index]
                current_client_index = (current_client_index + 1) % len(clients)
                
                # 对每个群组发送消息
                for group in TARGET_GROUPS:
                    success = await send_message(client, group, message)
                    if not success:
                        logging.warning(f"消息发送失败，跳过当前消息")
                        continue
            
            # 一轮发完后等待30-60分钟
            wait_time = random.uniform(1800, 3600)
            logging.info(f"本轮消息发送完成,等待 {wait_time/60:.1f} 分钟后开始下一轮...")
            await asyncio.sleep(wait_time)
            
    except KeyboardInterrupt:
        logging.info("收到停止信号，正在关闭...")
    except Exception as e:
        logging.error(f"运行出错: {str(e)}")
    finally:
        # 断开所有客户端连接
        for client in clients:
            try:
                await client.disconnect()
            except:
                pass

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n程序已停止") 