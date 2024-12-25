from telethon import TelegramClient
from telethon.tl.functions.channels import GetParticipantsRequest
from telethon.tl.types import ChannelParticipantsSearch
import os
import json
from datetime import datetime
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 创建 members 文件夹
MEMBERS_DIR = "members"
os.makedirs(MEMBERS_DIR, exist_ok=True)

# 从环境变量获取配置
api_id = int(os.getenv('API_ID'))
api_hash = os.getenv('API_HASH')

async def get_all_participants(client, channel, limit=None):
    """获取所有成员信息，不包括机器人"""
    participants = []
    bots_count = 0
    
    try:
        async for participant in client.iter_participants(channel):
            # 跳过机器人
            if participant.bot:
                bots_count += 1
                continue
                
            participants.append({
                'id': participant.id,
                'first_name': participant.first_name,
                'last_name': participant.last_name,
                'username': participant.username,
                'phone': participant.phone
            })
            
            if len(participants) % 100 == 0:
                print(f"已获取 {len(participants)} 个成员信息...")
            
            if limit and len(participants) >= limit:
                break
                
    except Exception as e:
        print(f"获取成员时出错: {e}")
    
    print(f"总共跳过 {bots_count} 个机器人")
    return participants

async def main():
    # 获取第一个可用的 session 文件
    sessions_dir = "sessions"
    session_files = [f for f in os.listdir(sessions_dir) if f.endswith('.session')]
    
    if not session_files:
        print("未找到任何 session 文件，请先运行 session_string.py 创建")
        return
        
    # 使用第一个 session 文件（不包含.session后缀）
    session_path = os.path.join(sessions_dir, session_files[0][:-8])
    print(f"使用 session 文件: {session_files[0]}")
    
    # 输入群组链接或 ID
    channel = input("请输入群组链接或 ID: ")
    
    async with TelegramClient(session_path, api_id, api_hash) as client:
        try:
            # 获取群组信息
            entity = await client.get_entity(channel)
            group_title = entity.title
            
            # 获取所有成员
            print(f"开始获取群组 {group_title} 的成员信息...")
            participants = await get_all_participants(client, channel)
            
            if participants:
                # 生成文件名（使用群组标题和时间戳）
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = os.path.join(MEMBERS_DIR, f"{group_title}_{timestamp}.json")
                
                # 保存成员信息
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(participants, f, ensure_ascii=False, indent=2)
                    
                print(f"成功保存 {len(participants)} 个成员信息到文件: {filename}")
            else:
                print("未获取到成员信息")
                
        except Exception as e:
            print(f"发生错误: {e}")

if __name__ == '__main__':
    import asyncio
    asyncio.run(main()) 