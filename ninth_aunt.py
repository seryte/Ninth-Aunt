#!/usr/bin/env python3

# -*- coding: utf-8 -*-

import re
import time
import json
import datetime
import logging
import logging.handlers
import requests
import random
import configparser
import argparse
import sys
import os
from typing import Dict, List, Optional, Tuple
from bs4 import BeautifulSoup
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5 as Cipher_PKCS1_v1_5
from base64 import b64decode, b64encode
from fake_useragent import UserAgent

class Config:
“”“配置管理类”””

```
def __init__(self, config_file: str = 'config.properties'):
    self.config_file = config_file
    self.config = configparser.ConfigParser()
    self.load_config()

def load_config(self):
    """加载配置文件"""
    if os.path.exists(self.config_file):
        self.config.read(self.config_file, encoding='utf-8')
    else:
        # 创建默认配置
        self.create_default_config()

def create_default_config(self):
    """创建默认配置文件"""
    self.config['DEFAULT'] = {
        'username': '',
        'password': '',
        'city_index': '',
        'unit_id': '',
        'unit_name': '',
        'dep_id': '',
        'dep_name': '',
        'doc_id': '',
        'doctor_name': '',
        'patient_name': '',
        'weeks': '1,2,3,4,5,6,7',
        'days': 'am,pm',
        'sleepTime': '3000',
        'brushStartDate': '',
        'enableAppoint': 'false',
        'appointTime': '',
        'brushChannel': '',
        'enableProxy': 'false',
        'proxyFilePath': '',
        'proxyMode': 'ROUND_ROBIN',
        'maxRetries': '3'
    }
    self.save_config()

def save_config(self):
    """保存配置到文件"""
    with open(self.config_file, 'w', encoding='utf-8') as f:
        self.config.write(f)

def get(self, key: str, default: str = '') -> str:
    """获取配置值"""
    return self.config.get('DEFAULT', key, fallback=default)

def set(self, key: str, value: str):
    """设置配置值"""
    if 'DEFAULT' not in self.config:
        self.config['DEFAULT'] = {}
    self.config['DEFAULT'][key] = value
    self.save_config()
```

class ProxyManager:
“”“代理管理类”””

```
def __init__(self, config: Config):
    self.config = config
    self.proxies = []
    self.current_index = 0
    self.load_proxies()

def load_proxies(self):
    """加载代理列表"""
    if not self.config.get('enableProxy') == 'true':
        return
    
    proxy_file = self.config.get('proxyFilePath')
    if not proxy_file or not os.path.exists(proxy_file):
        logging.warning("代理文件不存在或未配置")
        return
    
    try:
        with open(proxy_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    self.proxies.append(self.parse_proxy(line))
        
        logging.info(f"加载了 {len(self.proxies)} 个代理")
    except Exception as e:
        logging.error(f"加载代理文件失败: {e}")

def parse_proxy(self, proxy_line: str) -> Optional[Dict]:
    """解析代理配置"""
    try:
        # 格式: (http|socks)@ip:port
        if '@' in proxy_line:
            protocol, address = proxy_line.split('@', 1)
            return {
                'http': f'{protocol}://{address}',
                'https': f'{protocol}://{address}'
            }
    except:
        pass
    return None

def get_proxy(self) -> Optional[Dict]:
    """获取代理"""
    if not self.proxies:
        return None
    
    mode = self.config.get('proxyMode', 'ROUND_ROBIN')
    if mode == 'RANDOM':
        return random.choice(self.proxies)
    else:  # ROUND_ROBIN
        proxy = self.proxies[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.proxies)
        return proxy
```

class Channel:
“”“刷号通道枚举”””
CHANNEL_1 = “CHANNEL_1”
CHANNEL_2 = “CHANNEL_2”

class AutoRegister:
“”“91160自动挂号主类”””

```
def __init__(self, config_file: str = 'config.properties'):
    self.config = Config(config_file)
    self.proxy_manager = ProxyManager(self.config)
    self.session = requests.Session()
    self.ua = UserAgent()
    self.setup_logging()
    
    # 91160的RSA公钥
    self.PUBLIC_KEY = "MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDWuY4Gff8FO3BAKetyvNgGrdZM9CMNoe45SzHMXxAPWw6E2idaEjqe5uJFjVx55JW" \
                      "+5LUSGO1H5MdTcgGEfh62ink/cNjRGJpR25iVDImJlLi2izNs9zrQukncnpj6NGjZu" \
                      "/2z7XXfJb4XBwlrmR823hpCumSD1WiMl1FMfbVorQIDAQAB "
    
    # 城市数据
    self.cities = [
        {"name": "广州", "cityId": "2918"},
        {"name": "长沙", "cityId": "3274"},
        {"name": "香港", "cityId": "3314"},
        {"name": "上海", "cityId": "3306"},
        {"name": "武汉", "cityId": "3276"},
        {"name": "重庆", "cityId": "3316"},
        {"name": "北京", "cityId": "2912"},
        {"name": "东莞", "cityId": "2920"},
        {"name": "深圳", "cityId": "5"},
        {"name": "海外", "cityId": "6145"},
        {"name": "郑州", "cityId": "3242"},
        {"name": "天津", "cityId": "3308"},
        {"name": "淮南", "cityId": "3014"}
    ]
    
    # 星期数据
    self.weeks_list = [
        {"name": "星期一", "value": "1", "alias": "一"},
        {"name": "星期二", "value": "2", "alias": "二"},
        {"name": "星期三", "value": "3", "alias": "三"},
        {"name": "星期四", "value": "4", "alias": "四"},
        {"name": "星期五", "value": "5", "alias": "五"},
        {"name": "星期六", "value": "6", "alias": "六"},
        {"name": "星期天", "value": "7", "alias": "日"}
    ]

def setup_logging(self):
    """设置日志"""
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # 控制台输出
    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # 文件输出
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    file_handler = logging.handlers.RotatingFileHandler(
        'logs/91160-cli.log', maxBytes=10*1024*1024, backupCount=5, encoding='utf-8'
    )
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

def get_headers(self) -> Dict[str, str]:
    """获取请求头"""
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Referer": "https://www.91160.com",
        "Origin": "https://www.91160.com"
    }

def make_request(self, method: str, url: str, **kwargs) -> requests.Response:
    """发送请求（支持代理）"""
    proxy = self.proxy_manager.get_proxy()
    if proxy:
        kwargs['proxies'] = proxy
        logging.debug(f"使用代理: {proxy}")
    
    kwargs.setdefault('headers', self.get_headers())
    kwargs.setdefault('timeout', 10)
    
    return self.session.request(method, url, **kwargs)

def smart_delay(self):
    """智能延迟"""
    sleep_time = int(self.config.get('sleepTime', '3000')) / 1000
    delay = sleep_time + random.uniform(-0.5, 1.0)
    time.sleep(max(delay, 1.0))

def get_token(self) -> str:
    """获取登录token"""
    try:
        url = "https://user.91160.com/login.html"
        response = self.make_request('GET', url)
        response.encoding = response.apparent_encoding
        
        soup = BeautifulSoup(response.text, "html.parser")
        token_input = soup.find("input", id="tokens")
        
        if not token_input:
            raise ValueError("无法获取登录token")
        
        return token_input.attrs["value"]
    except Exception as e:
        logging.error(f"获取token失败: {e}")
        raise

def rsa_encrypt(self, text: str) -> str:
    """RSA加密"""
    try:
        rsa_key = RSA.importKey(b64decode(self.PUBLIC_KEY))
        cipher = Cipher_PKCS1_v1_5.new(rsa_key)
        encrypted = cipher.encrypt(text.encode())
        return b64encode(encrypted).decode()
    except Exception as e:
        logging.error(f"RSA加密失败: {e}")
        raise

def check_user(self, username: str, password: str, token: str) -> Dict:
    """检查用户状态"""
    url = "https://user.91160.com/checkUser.html"
    data = {
        "username": username,
        "password": password,
        "type": "m",
        "token": token
    }
    
    response = self.make_request('POST', url, data=data)
    
    try:
        return response.json()
    except:
        logging.error(f"checkUser响应不是有效JSON: {response.text[:200]}")
        return {"error": "响应格式错误"}

def login(self) -> bool:
    """登录"""
    username = self.config.get('username')
    password = self.config.get('password')
    
    if not username or not password:
        logging.error("用户名或密码未配置")
        return False
    
    try:
        # 1. 获取token
        token = self.get_token()
        logging.info("获取token成功")
        
        # 2. 检查用户
        check_result = self.check_user(username, password, token)
        if check_result.get('error'):
            logging.error(f"用户检查失败: {check_result}")
            return False
        
        # 3. RSA加密登录
        encrypted_username = self.rsa_encrypt(username)
        encrypted_password = self.rsa_encrypt(password)
        
        login_url = "https://user.91160.com/login.html"
        login_data = {
            "username": encrypted_username,
            "password": encrypted_password,
            "target": "https://www.91160.com",
            "error_num": 0,
            "tokens": token
        }
        
        response = self.make_request('POST', login_url, data=login_data, allow_redirects=False)
        
        if response.status_code == 302:
            redirect_url = response.headers.get("location", "")
            logging.info(f"登录重定向到: {redirect_url}")
            
            # 跟随重定向
            if redirect_url:
                redirect_response = self.make_request('GET', redirect_url, allow_redirects=False)
                if redirect_response.status_code == 302:
                    logging.info("登录成功")
                    return self.verify_login()
        
        logging.error("登录失败")
        return False
        
    except Exception as e:
        logging.error(f"登录异常: {e}")
        return False

def verify_login(self) -> bool:
    """验证登录状态"""
    try:
        url = "https://user.91160.com/order.html"
        response = self.make_request('GET', url)
        response.encoding = response.apparent_encoding
        
        soup = BeautifulSoup(response.text, "html.parser")
        username_element = soup.find(attrs={"class": "ac_user_name"})
        
        if username_element:
            logging.info(f"登录验证成功: {username_element.text}")
            return True
        
        return False
    except Exception as e:
        logging.error(f"验证登录状态失败: {e}")
        return False

def convert_week(self, week_value: str) -> str:
    """转换星期值"""
    for week in self.weeks_list:
        if week["value"] == week_value:
            return week["alias"]
    return ""

def brush_ticket_channel1(self, unit_id: str, dep_id: str, weeks: List[str], days: List[str]) -> List[Dict]:
    """通道1刷票 - 科室排班页"""
    start_date = self.config.get('brushStartDate')
    if start_date:
        base_date = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
    else:
        base_date = datetime.date.today()
    
    date_str = base_date.strftime("%Y-%m-%d")
    url = f"https://www.91160.com/dep/getschmast/uid-{unit_id}/depid-{dep_id}/date-{date_str}/p-0.html"
    
    try:
        response = self.make_request('GET', url)
        json_obj = response.json()
        
        if "week" not in json_obj:
            raise RuntimeError(f"通道1刷票异常: {json_obj}")
        
        week_list = json_obj["week"]
        week_indices = []
        for week in weeks:
            if week in week_list:
                week_indices.append(str(week_list.index(week)))
        
        doc_ids = json_obj["doc_ids"].split(",")
        result = []
        
        for doc_id in doc_ids:
            doc_schedule = json_obj["sch"][doc_id]
            for day in days:
                if day in doc_schedule:
                    schedule = doc_schedule[day]
                    if isinstance(schedule, list):
                        result.extend([s for s in schedule if s.get("y_state") == "1"])
                    else:
                        for week_idx in week_indices:
                            if week_idx in schedule:
                                sch_item = schedule[week_idx]
                                if sch_item.get("y_state") == "1":
                                    result.append(sch_item)
        
        return result
        
    except Exception as e:
        logging.error(f"通道1刷票失败: {e}")
        return []

def brush_ticket_channel2(self, doc_id: str, dep_id: str, weeks: List[str], days: List[str]) -> List[Dict]:
    """通道2刷票 - 医生详情页"""
    start_date = self.config.get('brushStartDate')
    if start_date:
        base_date = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
    else:
        base_date = datetime.date.today()
    
    date_str = base_date.strftime("%Y-%m-%d")
    url = "https://www.91160.com/doctors/ajaxgetclass.html"
    data = {
        "docid": doc_id,
        "date": date_str,
        "days": 6
    }
    
    try:
        response = self.make_request('POST', url, data=data)
        json_obj = response.json()
        
        if "dates" not in json_obj:
            if "status" in json_obj:
                logging.warning("Token过期，需要重新登录")
                return []
            raise RuntimeError(f"通道2刷票异常: {json_obj}")
        
        date_list = json_obj["dates"]
        week_dates = []
        
        for week in weeks:
            week_alias = self.convert_week(week)
            for date_key, week_name in date_list.items():
                if week_name == week_alias:
                    week_dates.append(date_key)
                    break
        
        if not week_dates:
            return []
        
        schedule_key = f"{dep_id}_{doc_id}"
        if schedule_key not in json_obj["sch"]:
            return []
        
        doc_schedule = json_obj["sch"][schedule_key]
        result = []
        
        for day in days:
            for date_key in week_dates:
                schedule_key = f"{dep_id}_{doc_id}_{day}"
                if schedule_key in doc_schedule:
                    day_schedule = doc_schedule[schedule_key]
                    if date_key in day_schedule:
                        schedule_item = day_schedule[date_key]
                        if schedule_item.get("y_state") == "1":
                            result.append(schedule_item)
        
        return result
        
    except Exception as e:
        logging.error(f"通道2刷票失败: {e}")
        return []

def brush_tickets(self) -> List[Dict]:
    """刷票 - 支持多通道"""
    unit_id = self.config.get('unit_id')
    dep_id = self.config.get('dep_id')
    doc_id = self.config.get('doc_id')
    weeks = self.config.get('weeks', '1,2,3,4,5,6,7').split(',')
    days = self.config.get('days', 'am,pm').split(',')
    
    brush_channel = self.config.get('brushChannel')
    tickets = []
    
    if brush_channel == Channel.CHANNEL_1:
        tickets = self.brush_ticket_channel1(unit_id, dep_id, weeks, days)
    elif brush_channel == Channel.CHANNEL_2:
        tickets = self.brush_ticket_channel2(doc_id, dep_id, weeks, days)
    else:
        # 默认两个通道轮询
        tickets_1 = self.brush_ticket_channel1(unit_id, dep_id, weeks, days)
        tickets_2 = self.brush_ticket_channel2(doc_id, dep_id, weeks, days)
        tickets = tickets_1 + tickets_2
    
    return tickets

def book_appointment(self, ticket: Dict) -> bool:
    """预约挂号"""
    try:
        unit_id = self.config.get('unit_id')
        dep_id = self.config.get('dep_id')
        schedule_id = ticket["schedule_id"]
        
        # 1. 获取预约页面
        step1_url = f"https://www.91160.com/guahao/ystep1/uid-{unit_id}/depid-{dep_id}/schid-{schedule_id}.html"
        response = self.make_request('GET', step1_url)
        response.encoding = response.apparent_encoding
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # 2. 提取必要参数
        sch_data_input = soup.find(attrs={"name": "sch_data"})
        mid_input = soup.find(attrs={"name": "mid"})
        detl_elements = soup.select('#delts li')
        detlid_realtime_input = soup.find("input", id="detlid_realtime")
        
        if not all([sch_data_input, mid_input, detl_elements, detlid_realtime_input]):
            logging.error("无法获取预约必要参数")
            return False
        
        # 3. 构造预约数据
        appointment_data = {
            "sch_data": sch_data_input.attrs["value"],
            "mid": mid_input.attrs["value"],
            "hisMemId": "",
            "disease_input": "",
            "order_no": "",
            "disease_content": "",
            "accept": "1",
            "unit_id": ticket["unit_id"],
            "schedule_id": ticket["schedule_id"],
            "dep_id": ticket["dep_id"],
            "his_dep_id": "",
            "sch_date": "",
            "time_type": ticket["time_type"],
            "doctor_id": ticket["doctor_id"],
            "his_doc_id": "",
            "detlid": detl_elements[0].attrs["val"],
            "detlid_realtime": detlid_realtime_input.attrs["value"],
            "level_code": ticket["level_code"],
            "is_hot": "",
            "addressId": "3317",
            "address": "China",
            "buyinsurance": 1
        }
        
        # 4. 提交预约
        submit_url = "https://www.91160.com/guahao/ysubmit.html"
        response = self.make_request('POST', submit_url, data=appointment_data, allow_redirects=False)
        
        if response.status_code == 302:
            redirect_url = response.headers.get("location", "")
            logging.info(f"预约提交重定向到: {redirect_url}")
            
            if redirect_url != "https://www.91160.com":
                logging.info("🎉 预约成功！")
                return True
            else:
                logging.info("预约失败，继续尝试")
                return False
        else:
            logging.error(f"预约失败，状态码: {response.status_code}")
            return False
            
    except Exception as e:
        logging.error(f"预约异常: {e}")
        return False

def wait_for_appointment_time(self) -> bool:
    """等待定时预约时间"""
    if self.config.get('enableAppoint') != 'true':
        return True
    
    appoint_time_str = self.config.get('appointTime')
    if not appoint_time_str:
        return True
    
    try:
        appoint_time = datetime.datetime.strptime(appoint_time_str, "%Y-%m-%d %H:%M:%S")
        now = datetime.datetime.now()
        
        if now < appoint_time:
            wait_seconds = (appoint_time - now).total_seconds()
            logging.info(f"等待定时预约时间: {appoint_time_str}，还需等待 {wait_seconds:.1f} 秒")
            time.sleep(wait_seconds)
            logging.info("到达预约时间，开始抢号！")
        
        return True
    except ValueError:
        logging.error(f"定时预约时间格式错误: {appoint_time_str}")
        return False

def register(self) -> bool:
    """开始挂号"""
    # 1. 登录
    if not self.login():
        logging.error("登录失败，无法继续")
        return False
    
    # 2. 等待定时预约
    if not self.wait_for_appointment_time():
        return False
    
    # 3. 开始刷票
    logging.info("开始刷票...")
    max_retries = int(self.config.get('maxRetries', '3'))
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            # 刷票
            tickets = self.brush_tickets()
            
            if tickets:
                logging.info(f"发现 {len(tickets)} 张可用号源")
                
                # 随机选择一个票
                selected_ticket = random.choice(tickets)
                logging.info(f"选择预约: {selected_ticket}")
                
                # 尝试预约
                if self.book_appointment(selected_ticket):
                    logging.info("🎉 挂号成功！")
                    return True
                else:
                    logging.info("本次预约失败，继续刷票...")
            else:
                logging.info("暂无可用号源，继续刷票...")
            
            # 延迟后继续
            self.smart_delay()
            
        except Exception as e:
            logging.error(f"刷票过程出错: {e}")
            retry_count += 1
            if retry_count < max_retries:
                logging.info(f"重试中... ({retry_count}/{max_retries})")
                time.sleep(10)
    
    logging.error("达到最大重试次数，挂号失败")
    return False

def init_config(self):
    """初始化配置"""
    print("=== 91160挂号配置初始化 ===\n")
    
    # 用户名密码
    username = input("请输入用户名: ").strip()
    password = input("请输入密码: ").strip()
    self.config.set('username', username)
    self.config.set('password', password)
    
    # 城市选择
    print("\n请选择城市:")
    for i, city in enumerate(self.cities, 1):
        print(f"{i:2d}. {city['name']}")
    
    while True:
        try:
            city_choice = int(input("\n请输入城市编号: ")) - 1
            if 0 <= city_choice < len(self.cities):
                self.config.set('city_index', str(city_choice))
                break
            else:
                print("编号无效，请重新输入")
        except ValueError:
            print("请输入有效数字")
    
    # 这里可以继续添加医院、科室、医生的选择逻辑
    # 为了简化，先设置默认值
    print("\n配置初始化完成！")
    print("请手动编辑 config.properties 文件完善其他配置项")
```

def main():
parser = argparse.ArgumentParser(description=‘91160自动挂号CLI工具’)
parser.add_argument(‘command’, choices=[‘init’, ‘register’], help=‘执行命令’)
parser.add_argument(’-c’, ‘–config’, default=‘config.properties’, help=‘配置文件路径’)

```
args = parser.parse_args()

try:
    app = AutoRegister(args.config)
    
    if args.command == 'init':
        app.init_config()
    elif args.command == 'register':
        success = app.register()
        sys.exit(0 if success else 1)
        
except KeyboardInterrupt:
    logging.info("用户中断程序")
    sys.exit(0)
except Exception as e:
    logging.error(f"程序异常: {e}")
    sys.exit(1)
```

if **name** == ‘**main**’:
main()
