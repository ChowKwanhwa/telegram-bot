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

# 代理列表
PROXY_LIST = [
    {
        'addr': "119.42.39.170",
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

async def test_session_with_proxy(session_file, proxy_config):
    """使用指定代理测试单个会话文件"""
    session_path = os.path.join(SESSIONS_DIR, session_file.replace('.session', ''))
    
    # 构建代理配置
    proxy = {
        'proxy_type': 'socks5',
        'addr': proxy_config['addr'],
        'port': proxy_config['port'],
        'username': proxy_config['username'],
        'password': proxy_config['password']
    }
    
    try:
        # 创建客户端并添加代理配置
        client = TelegramClient(session_path, API_ID, API_HASH, proxy=proxy)
        
        # 尝试连接
        print(f"\n正在使用代理 {proxy_config['addr']}:{proxy_config['port']} 测试 {session_file}...")
        await client.connect()
        
        # 检查是否已授权
        if await client.is_user_authorized():
            # 获取账号信息
            me = await client.get_me()
            username = f"@{me.username}" if me.username else me.id
            print(f"✅ {session_file} 连接成功!")
            print(f"   账号信息: {username}")
            print(f"   手机号: {me.phone}")
            await client.disconnect()
            return True, session_file, "有效"
            
        else:
            print(f"❌ {session_file} 未授权!")
            await client.disconnect()
            return False, session_file, "未授权"
        
    except Exception as e:
        print(f"❌ 使用代理 {proxy_config['addr']} 测试失败: {str(e)}")
        return False, session_file, "连接失败"

async def test_session(session_file):
    """尝试使用所有代理测试会话文件"""
    for proxy in PROXY_LIST:
        success, session, status = await test_session_with_proxy(session_file, proxy)
        if success:
            return session, status
    
    return session_file, "所有代理均失败"

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