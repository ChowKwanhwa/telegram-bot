from telethon import TelegramClient, functions, errors
import csv
from datetime import datetime
import asyncio
import os
from dotenv import load_dotenv
import pandas as pd
import random

# 加载.env文件
load_dotenv()

# 从环境变量获取配置
api_id = int(os.getenv('API_ID'))
api_hash = os.getenv('API_HASH')

# 配置
SESSION_FILE = 'session.session'
TARGET_GROUP = '@johnstones12344'
CSV_FILE = 'active_users.csv'

async def add_contact(client, username):
    """将用户添加为联系人"""
    try:
        if not username.startswith('@'):
            username = f'@{username}'
            
        user = await client.get_entity(username)
        
        await client(functions.contacts.AddContactRequest(
            id=user.id,
            first_name=user.first_name or username,
            last_name="",
            phone="",
            add_phone_privacy_exception=False
        ))
        print(f"成功添加联系人: {username}")
        return True
        
    except errors.FloodWaitError as e:
        print(f"需要等待 {e.seconds} 秒后继续")
        await asyncio.sleep(e.seconds)
        return False
    except Exception as e:
        print(f"添加联系人 {username} 时出错: {str(e)}")
        return False

async def add_user_to_group(client, username, target_group):
    """将用户添加到目标群组"""
    try:
        if not username.startswith('@'):
            username = f'@{username}'
            
        target_entity = await client.get_entity(target_group)
        user_to_add = await client.get_entity(username)
        
        await client(functions.channels.InviteToChannelRequest(
            channel=target_entity,
            users=[user_to_add]
        ))
        print(f"成功添加用户 {username} 到 {target_group}")
        return True
        
    except errors.FloodWaitError as e:
        print(f"需要等待 {e.seconds} 秒后继续")
        await asyncio.sleep(e.seconds)
        return False
    except errors.UserPrivacyRestrictedError:
        print(f"用户 {username} 的隐私设置限制了邀请")
        return True
    except errors.UserNotMutualContactError:
        print(f"用户 {username} 需要是相互联系人")
        return True
    except errors.UserChannelsTooMuchError:
        print(f"用户 {username} 加入的群组已达上限")
        return True
    except errors.RPCError as e:
        if "Too many requests" in str(e):
            print(f"添加用户 {username} 时遇到限制，等待后重试")
            return False
        else:
            print(f"添加用户 {username} 时出错: {str(e)}")
            return True
    except Exception as e:
        print(f"添加用户 {username} 时出错: {str(e)}")
        return True

async def main():
    client = TelegramClient(SESSION_FILE, api_id, api_hash)
    
    try:
        await client.start()
        me = await client.get_me()
        print(f"已登录账号: {me.first_name} (@{me.username})")
        
        # 读取CSV文件
        df = pd.read_csv(CSV_FILE)
        
        # 过滤掉机器人账号（通常包含 'bot' 在用户名中）
        df = df[~df['user_id'].str.contains('bot', case=False, na=False)]
        
        # 获取唯一的username列表（从user_id列）
        usernames = df['user_id'].unique()
        
        # 过滤掉无效的用户名
        valid_usernames = []
        for username in usernames:
            if pd.isna(username) or not isinstance(username, str):
                continue
            if len(username) >= 4 and username.isalnum():  # 基本的用户名验证
                valid_usernames.append(username)
        
        print(f"从CSV中读取到 {len(valid_usernames)} 个有效的唯一用户名")
        
        # 添加联系人并拉进群组
        contact_count = 0
        added_count = 0
        print("\n开始添加联系人并拉进群组...")
        for username in valid_usernames:
            # 添加联系人
            if await add_contact(client, username):
                contact_count += 1
                
                # 随机等待时间
                wait_time = random.uniform(20, 40)
                print(f"等待 {wait_time:.2f} 秒...")
                await asyncio.sleep(wait_time)
                
                # 添加到群组
                if await add_user_to_group(client, username, TARGET_GROUP):
                    added_count += 1
            
            # 随机等待时间
            wait_time = random.uniform(30, 60)
            print(f"等待 {wait_time:.2f} 秒...")
            await asyncio.sleep(wait_time)
            
        print(f"\n完成添加用户")
        print(f"联系人添加成功: {contact_count}/{len(valid_usernames)}")
        print(f"群组成员添加成功: {added_count}/{len(valid_usernames)}")
        
    except Exception as e:
        print(f"运行出错: {str(e)}")
    finally:
        await client.disconnect()

if __name__ == '__main__':
    # 配置事件循环
    if os.name == 'nt':  # Windows
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    # 运行主程序
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n程序被用户中断") 