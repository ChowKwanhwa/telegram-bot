from telethon import TelegramClient, events
from telethon.tl.types import User, Channel, PeerChannel
from telethon.tl.functions.channels import GetParticipantsRequest
from telethon.tl.types import ChannelParticipantsRecent
import csv
from datetime import datetime
import os
from dotenv import load_dotenv
import logging
import asyncio
from telethon.tl.functions.channels import JoinChannelRequest

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('member_monitor.log')
    ]
)

# 加载环境变量
load_dotenv()

# 配置
API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')
TARGET_GROUP = "@fw147group"  # 替换为你要监控的群组链接
SESSIONS_DIR = "sessions"
CSV_FILE = "new_members.csv"

# 代理列表配置
PROXY_LIST = [
    {
        'proxy_type': 'socks5',
        'addr': '119.42.39.170',
        'port': 5798,
        'username': 'Maomaomao77',
        'password': 'Maomaomao77'
    },
    {
        'addr': "86.38.26.189",
        'port': 6354,
        'username': 'binghua99',
        'password': 'binghua99'
    },
    {
        'addr': "198.105.111.87",
        'port': 6765,
        'username': 'binghua99',
        'password': 'binghua99'
    },
    {
        'addr': "185.236.95.32",
        'port': 5993,
        'username': 'binghua99',
        'password': 'binghua99'
    }
]

async def try_connect_with_proxy(session_path, proxy_config):
    """尝试使用特定代理连接"""
    client = TelegramClient(session_path, API_ID, API_HASH, proxy=proxy_config)
    
    try:
        logging.info(f"正在尝试使用代理 {proxy_config['addr']}:{proxy_config['port']} 连接...")
        await client.connect()
        
        if await client.is_user_authorized():
            me = await client.get_me()
            logging.info(f"[成功] 使用代理 {proxy_config['addr']} 连接成功!")
            logging.info(f"       账号: {me.first_name} (@{me.username})")
            return client
        
        await client.disconnect()
        logging.error(f"[失败] 使用代理 {proxy_config['addr']} 连接失败: 未授权")
        return None
        
    except Exception as e:
        logging.error(f"[失败] 使用代理 {proxy_config['addr']} 连接失败: {str(e)}")
        try:
            await client.disconnect()
        except:
            pass
        return None

def save_to_csv(user_data):
    """保存用户数据到CSV文件"""
    file_exists = os.path.exists(CSV_FILE)
    
    # 更新字段列表，添加 join_type
    fieldnames = ['timestamp', 'user_id', 'username', 'first_name', 'last_name', 'join_type']
    
    with open(CSV_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(user_data)

async def join_group(client, group_link):
    """尝试加入群组"""
    try:
        logging.info(f"正在尝试加入群组 {group_link}...")
        entity = await client.get_entity(group_link)
        await client(JoinChannelRequest(entity))
        logging.info(f"成功加入群组 {group_link}")
        return True
    except Exception as e:
        logging.error(f"加入群组失败: {str(e)}")
        return False

async def main():
    # 获取第一个可用的 session 文件
    session_files = [f for f in os.listdir(SESSIONS_DIR) if f.endswith('.session')]
    
    if not session_files:
        logging.error("未找到任何 session 文件，请先创建 session")
        return
        
    # 使用第一个 session 文件
    session_path = os.path.join(SESSIONS_DIR, session_files[0][:-8])
    logging.info(f"使用 session 文件: {session_files[0]}")
    
    # 尝试所有代理
    client = None
    for proxy in PROXY_LIST:
        client = await try_connect_with_proxy(session_path, proxy)
        if client:
            break
    
    if not client:
        logging.error("所有代理均连接失败!")
        return

    try:
        # 先尝试加入群组
        if not await join_group(client, TARGET_GROUP):
            logging.error("无法加入目标群组，退出监控")
            return

        # 获取目标群组
        try:
            group = await client.get_entity(TARGET_GROUP)
            actual_username = group.username if group.username else ''
            
            # 严格检查群组用户名是否完全匹配
            if actual_username != TARGET_GROUP.replace("@", ""):
                logging.error(f"群组不匹配!")
                logging.error(f"目标群组: {TARGET_GROUP}")
                logging.error(f"实际群组: @{actual_username}")
                logging.error("请确保群组用户名完全匹配，包括数字后缀")
                return
                
            logging.info(f"成功连接到目标群组: {TARGET_GROUP}")
            logging.info(f"群组标题: {group.title}")
            logging.info(f"群组 ID: {group.id}")
            
        except ValueError as e:
            logging.error(f"无法找到群组 {TARGET_GROUP}")
            logging.error(f"错误信息: {str(e)}")
            return
        except Exception as e:
            logging.error(f"连接群组时出错: {str(e)}")
            return

        # 注册所有可能的新成员事件
        @client.on(events.ChatAction)
        async def handler(event):
            try:
                # 获取事件类型
                event_type = "未知事件"
                if event.user_joined:
                    event_type = "用户主动加入"
                elif event.user_added:
                    event_type = "用户被邀请加入"
                elif event.user_left:
                    event_type = "用户离开"
                elif event.user_kicked:
                    event_type = "用户被踢出"
                
                logging.info(f"检测到群组事件: {event_type}")
                
                if event.user_joined or event.user_added:
                    chat = await event.get_chat()
                    user = await event.get_user()
                    
                    logging.info(f"群组: {chat.title} (@{chat.username})")
                    logging.info(f"群组 ID: {chat.id}")
                    logging.info(f"用户: {user.first_name} (@{user.username})")
                    logging.info(f"用户 ID: {user.id}")
                    
                    if chat.username == TARGET_GROUP.replace("@", ""):
                        user_data = {
                            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'user_id': user.id,
                            'username': user.username or '',
                            'first_name': user.first_name or '',
                            'last_name': user.last_name or '',
                            'join_type': event_type
                        }
                        save_to_csv(user_data)
                        logging.info("[成功] 已记录新成员信息到 CSV")
                    else:
                        logging.info("[跳过] 忽略非目标群组事件")
                        
            except Exception as e:
                logging.error(f"处理事件时出错: {str(e)}")
                logging.error("错误详情: ", exc_info=True)

        # 修改测试事件处理器
        @client.on(events.NewMessage(chats=TARGET_GROUP))
        async def test_handler(event):
            chat = await event.get_chat()
            logging.debug(f"收到来自 {chat.title} 的新消息")  # 改为 debug 级别，减少干扰

        logging.info(f"[开始] 开始监控群组 {TARGET_GROUP}")
        logging.info(f"[信息] 新成员信息将保存到: {os.path.abspath(CSV_FILE)}")
        logging.info("[等待] 等待新成员加入事件...")
        
        await client.run_until_disconnected()
        
    except Exception as e:
        logging.error(f"运行出错: {str(e)}")
        logging.error("错误详情: ", exc_info=True)
    finally:
        await client.disconnect()

if __name__ == '__main__':
    asyncio.run(main()) 