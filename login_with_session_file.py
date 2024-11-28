from telethon import TelegramClient, functions, errors
import asyncio
import argparse
from telethon.tl.functions.photos import UploadProfilePhotoRequest
from telethon.tl.functions.account import UpdateProfileRequest, UpdateUsernameRequest
import aiohttp
import io
from dotenv import load_dotenv
import os
# 加载.env文件
load_dotenv()

# 从环境变量获取配置
api_id = int(os.getenv('API_ID'))
api_hash = os.getenv('API_HASH')

SESSION_FILE = '27847052889.session'
TARGET_USERNAME = '@peanutButter453'

# 要发送的消息列表
messages = [
    "Hello! I just joined this group!",
    "这是自动发送的消息",
    "测试消息3"
]

# 个人资料设置
profile_settings = {
    'first_name': 'gimbo',
    'last_name': 'gimbo',
    'username': 'gimbobobno123',  # 不需要@符号
    'photo_url': 'https://images.unsplash.com/photo-1721332155484-5aa73a54c6d2?q=80&w=1935&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDF8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D'  # Unsplash随机图片
}

async def download_image(url):
    """从URL下载图片"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    return io.BytesIO(await response.read())
                else:
                    print(f"下载图片失败，状态码: {response.status}")
                    return None
    except Exception as e:
        print(f"下载图片时出错: {str(e)}")
        return None

async def update_profile(client):
    """更新个人资料"""
    try:
        # 更新名字
        await client(UpdateProfileRequest(
            first_name=profile_settings['first_name'],
            last_name=profile_settings['last_name']
        ))
        print(f"成功更新名字为: {profile_settings['first_name']} {profile_settings['last_name']}")

        # 更新用户名
        try:
            await client(UpdateUsernameRequest(username=profile_settings['username']))
            print(f"成功更新用户名为: @{profile_settings['username']}")
        except errors.UsernameOccupiedError:
            print("错误：该用户名已被占用")
        except Exception as e:
            print(f"更新用户名失败: {str(e)}")

        # 更新头像
        try:
            # 下载图片
            photo_data = await download_image(profile_settings['photo_url'])
            if photo_data:
                # 保存到本地文件
                with open('profile/dog1.jpg', 'wb') as f:
                    f.write(photo_data.getvalue())
                
                # 上传头像
                await client(UploadProfilePhotoRequest(
                    file=await client.upload_file('profile/dog1.jpg')
                ))
                print("成功更新头像")
            else:
                print("无法更新头像：图片下载失败")
        except Exception as e:
            print(f"更新头像失败: {str(e)}")

    except Exception as e:
        print(f"更新个人资料时出错: {str(e)}")

async def join_chat(client, username):
    """尝试加入群组"""
    try:
        entity = await client.get_entity(username)
        await client(functions.channels.JoinChannelRequest(entity))
        print(f"成功加入: {username}")
        return True
    except errors.ChatWriteForbiddenError:
        print("错误：没有权限在此群组发送消息")
        return False
    except errors.UserAlreadyParticipantError:
        print("已经是群组成员")
        return True
    except Exception as e:
        print(f"加入群组失败: {str(e)}")
        return False

async def main(update_profile_only=False):
    client = TelegramClient(SESSION_FILE, api_id, api_hash)
    
    try:
        await client.start()
        me = await client.get_me()
        print(f"已登录账号: {me.first_name} (@{me.username})")

        if update_profile_only:
            # 仅更新个人资料
            await update_profile(client)
        else:
            # 执行加入群组和发送消息的功能
            if await join_chat(client, TARGET_USERNAME):
                print("等待5秒后开始发送消息...")
                await asyncio.sleep(5)
                
                for message in messages:
                    try:
                        await client.send_message(TARGET_USERNAME, message)
                        print(f"成功发送消息: {message}")
                        await asyncio.sleep(2)
                    except Exception as e:
                        print(f"发送消息失败: {str(e)}")
            else:
                print("由于无法加入群组，消息发送取消")
                
    except Exception as e:
        print(f"运行出错: {str(e)}")
    finally:
        await client.disconnect()

if __name__ == '__main__':
    # 设置命令行参数
    parser = argparse.ArgumentParser(description='Telegram自动化脚本')
    parser.add_argument('--profile', action='store_true', 
                      help='仅更新个人资料（头像、名字和用户名）')
    args = parser.parse_args()

    # 运行主程序
    asyncio.run(main(update_profile_only=args.profile))
