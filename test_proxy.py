import socket
import socks
import requests
import time
from typing import List, Dict, Tuple

def test_socks5_proxy(addr: str, port: int, username: str = None, password: str = None) -> Tuple[bool, float]:
    """测试单个SOCKS5代理"""
    print(f"\n开始测试代理: {addr}:{port}")
    print(f"认证信息: {'使用认证' if username and password else '无认证'}")
    
    try:
        # 构建代理URL
        proxy_url = f'socks5://{username}:{password}@{addr}:{port}' if username and password else f'socks5://{addr}:{port}'
        proxies = {
            'http': proxy_url,
            'https': proxy_url
        }
        print(f"代理设置: {proxy_url}")

        # 测试网站列表
        test_urls = [
            'http://api.ipify.org?format=json',
            'http://www.baidu.com',
            'https://www.google.com',
            'http://example.com'
        ]
        
        for url in test_urls:
            try:
                print(f"\n尝试访问: {url}")
                start_time = time.time()
                response = requests.get(
                    url, 
                    proxies=proxies,
                    timeout=30,
                    verify=False
                )
                
                elapsed_time = time.time() - start_time
                print(f"响应状态码: {response.status_code}")
                print(f"响应内容长度: {len(response.content)} bytes")
                
                if 'ipify' in url:
                    print(f"当前 IP: {response.text}")
                
                if response.status_code == 200:
                    return True, elapsed_time
                
            except Exception as e:
                print(f"访问失败: {str(e)}")
                continue
        
    except Exception as e:
        print(f"代理设置失败: {str(e)}")
    
    return False, float('inf')

def test_proxy_list(proxy_list: List[Dict]) -> List[Dict]:
    """测试代理列表，返回可用代理"""
    working_proxies = []
    
    print("开始测试代理列表...\n")
    
    for i, proxy in enumerate(proxy_list, 1):
        addr = proxy['addr']
        port = proxy['port']
        username = proxy.get('username')  # 使用 get() 方法安全获取可选参数
        password = proxy.get('password')
        
        print(f"测试代理 [{i}/{len(proxy_list)}]: {addr}:{port}")
        
        try:
            is_working, speed = test_socks5_proxy(addr, port, username, password)
            
            if is_working:
                print(f"✓ 代理可用! 响应时间: {speed:.2f}秒")
                working_proxies.append({
                    'addr': addr,
                    'port': port,
                    'speed': speed
                })
            else:
                print("✗ 代理不可用")
                
        except Exception as e:
            print(f"✗ 测试出错: {str(e)}")
        
        print("-" * 50)
    
    return working_proxies

if __name__ == "__main__":
    # 测试代理列表
    test_proxies = [
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
    
    # 禁用 SSL 警告
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    # 测试所有代理
    working_proxies = test_proxy_list(test_proxies)
    
    # 显示测试结果
    print("\n测试结果汇总:")
    print(f"总共测试: {len(test_proxies)} 个代理")
    print(f"可用代理: {len(working_proxies)} 个")
    
    if working_proxies:
        print("\n可用代理列表:")
        # 按速度排序
        working_proxies.sort(key=lambda x: x['speed'])
        for i, proxy in enumerate(working_proxies, 1):
            print(f"{i}. {proxy['addr']}:{proxy['port']} (响应时间: {proxy['speed']:.2f}秒)") 