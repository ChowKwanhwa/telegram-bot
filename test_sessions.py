import os
from telethon import TelegramClient
import asyncio
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 获取API凭据
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")

# 会话目录
SESSIONS_DIR = "sessions"

async def test_session(session_file):
    """测试单个会话文件"""
    session_path = os.path.join(SESSIONS_DIR, session_file.replace('.session', ''))
    
    # 添加代理配置
    proxy = {
        'proxy_type': 'socks5',
        'addr': '132.148.167.243',
        'port': 40349,
    }
    
    try:
        # 创建客户端并添加代理配置
        client = TelegramClient(session_path, API_ID, API_HASH, proxy=proxy)
        
        # 尝试连接
        print(f"\n正在测试 {session_file}...")
        await client.connect()
        
        # 检查是否已授权
        if await client.is_user_authorized():
            # 获取账号信息
            me = await client.get_me()
            username = f"@{me.username}" if me.username else me.id
            print(f"✅ {session_file} 连接成功!")
            print(f"   账号信息: {username}")
            print(f"   手机号: {me.phone}")
            status = "有效"
        else:
            print(f"❌ {session_file} 未授权!")
            status = "未授权"
            
        await client.disconnect()
        return session_file, status
        
    except Exception as e:
        print(f"❌ {session_file} 测试失败: {str(e)}")
        return session_file, "无效"

async def main():
    print("开始测试会话文件...\n")
    
    # 确保sessions目录存在
    if not os.path.exists(SESSIONS_DIR):
        print(f"错误: {SESSIONS_DIR} 目录不存在!")
        return
        
    # 获取所有.session文件
    session_files = [f for f in os.listdir(SESSIONS_DIR) if f.endswith('.session')]
    
    if not session_files:
        print(f"在 {SESSIONS_DIR} 目录中没有找到.session文件!")
        return
        
    print(f"找到 {len(session_files)} 个会话文件")
    
    # 测试所有会话
    results = []
    for session_file in session_files:
        result = await test_session(session_file)
        results.append(result)
    
    # 打印总结报告
    print("\n=== 测试报告 ===")
    print(f"总共测试: {len(results)} 个会话文件")
    valid = sum(1 for _, status in results if status == "有效")
    print(f"有效会话: {valid}")
    print(f"无效会话: {len(results) - valid}")
    
    # 打印详细状态
    print("\n详细状态:")
    for session_file, status in results:
        print(f"{session_file}: {status}")

if __name__ == "__main__":
    asyncio.run(main()) 