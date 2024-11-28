from telethon import TelegramClient, functions
import csv
from datetime import datetime
import asyncio
import os
from dotenv import load_dotenv

# 加载.env文件
load_dotenv()

# 从环境变量获取配置
api_id = int(os.getenv('API_ID'))
api_hash = os.getenv('API_HASH')

# 配置
SESSION_FILE = 'session.session'
SOURCE_GROUPS = [
    '@MEXCEnglish',
    # '@lipeixiamaoqi'
]

# CSV 文件配置
CSV_FILE = 'members.csv'
CSV_HEADERS = ['group_name', 'user_id', 'username', 'first_name', 'last_name', 'is_bot', 'timestamp']

async def save_to_csv(members_data):
    """保存用户数据到CSV文件"""
    file_exists = os.path.exists(CSV_FILE)
    
    with open(CSV_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
        if not file_exists:
            writer.writeheader()
        writer.writerows(members_data)
    print(f"已保存数据到 {CSV_FILE}")

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

async def get_members(client, group):
    """获取群组成员列表"""
    try:
        print(f"\n正在获取 {group} 的成员列表...")
        entity = await client.get_entity(group)
        members_data = []
        
        async for user in client.iter_participants(entity):
            member = {
                'group_name': group,
                'user_id': user.id,
                'username': user.username or '',
                'first_name': user.first_name or '',
                'last_name': user.last_name or '',
                'is_bot': user.bot,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            members_data.append(member)
            
            # 打印进度
            if len(members_data) % 100 == 0:
                print(f"已获取 {len(members_data)} 个成员...")
        
        print(f"完成获取 {group} 的成员列表，共 {len(members_data)} 个成员")
        return members_data
        
    except Exception as e:
        print(f"获取群组 {group} 成员列表时出错: {str(e)}")
        return []

async def main():
    client = TelegramClient(SESSION_FILE, api_id, api_hash)
    
    try:
        await client.start()
        me = await client.get_me()
        print(f"已登录账号: {me.first_name} (@{me.username})")
        
        # 先加入所有群组
        for group in SOURCE_GROUPS:
            if not await join_group(client, group):
                print(f"警告: 无法加入群组 {group}，将跳过获取其成员列表")
                continue
            
            # 等待一下再获取成员列表
            await asyncio.sleep(2)
            
            try:
                # 获取成员列表
                members = await get_members(client, group)
                if members:
                    # 保存到CSV
                    await save_to_csv(members)
                    print(f"{group} 的成员数据已保存")
                
                # 添加延时以避免请求过快
                await asyncio.sleep(2)
                
            except Exception as e:
                print(f"处理群组 {group} 时出错: {str(e)}")
                continue
        
    except Exception as e:
        print(f"运行出错: {str(e)}")
    finally:
        await client.disconnect()

if __name__ == '__main__':
    asyncio.run(main())
