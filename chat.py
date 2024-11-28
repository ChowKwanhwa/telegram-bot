from telethon import TelegramClient, errors
from telethon.sessions import StringSession
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from dotenv import load_dotenv
import os
# 加载.env文件
load_dotenv()

# 从环境变量获取配置
api_id = int(os.getenv('API_ID'))
api_hash = os.getenv('API_HASH')
TARGET_GROUP = '@testserverbotr'

# 如果有现成的session string，直接填在这里
SESSION_STRING = None  # 首次运行后，将打印的session string复制到这里

# 要发送的消息列表
messages = [
    "测试消息1",
    "测试消息2",
    "测试消息3"
]

async def verify_group(client):
    """验证群组是否可访问"""
    try:
        entity = await client.get_entity(TARGET_GROUP)
        print(f"成功找到群组: {entity.title}")
        return True
    except errors.UsernameNotOccupiedError:
        print("错误：指定的用户名不存在")
        return False
    except errors.UsernameInvalidError:
        print("错误：无效的用户名格式")
        return False
    except Exception as e:
        print(f"验证群组时出错: {str(e)}")
        return False

async def send_messages(client):
    """发送消息"""
    try:
        # 首先验证群组
        if not await verify_group(client):
            return

        # 发送消息
        for message in messages:
            try:
                await client.send_message(TARGET_GROUP, message)
                print(f"成功发送消息: {message}")
                # 添加延时以避免发送太快
                await asyncio.sleep(2)
            except errors.FloodWaitError as e:
                print(f"发送太频繁，需要等待 {e.seconds} 秒")
                await asyncio.sleep(e.seconds)
            except Exception as e:
                print(f"发送消息失败: {str(e)}")
                
    except Exception as e:
        print(f"发送过程中出错: {str(e)}")

async def main():
    """主函数"""
    if SESSION_STRING:
        # 使用已有的session string创建客户端
        client = TelegramClient(StringSession(SESSION_STRING), api_id, api_hash)
    else:
        # 首次运行，创建新的session
        client = TelegramClient(StringSession(), api_id, api_hash)
    
    try:
        # 启动客户端
        await client.start()
        
        # 如果是首次运行，打印session string
        if not SESSION_STRING:
            print("\n=== 请保存以下session string ===")
            print(client.session.save())
            print("=== 将此字符串复制到SESSION_STRING变量中 ===\n")
        
        # 获取当前账号信息
        me = await client.get_me()
        print(f'已登录账号: {me.first_name} (@{me.username})')
        
        # 发送消息
        await send_messages(client)
        
    except Exception as e:
        print(f"运行过程中出错: {str(e)}")
    finally:
        await client.disconnect()

if __name__ == '__main__':
    # 运行主程序
    asyncio.run(main())
