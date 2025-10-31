# govee_community_tool/core/account_generator.py

import time
import random
import string
import json
import requests
from typing import Dict, List, Tuple

# 禁用 InsecureRequestWarning
import urllib3

from gui.widgets import log_text

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class AccountGenerator:
    def __init__(self, base_url: str,log_widget):
        self.base_url = base_url
        self.headers = {
            'clientId': '5e972a68a408cada',
            'clientType': '0',
            'country': 'US',
            'Content-Type': 'application/json',
            'timestamp': str(int(time.time() * 1000))
        }
        self.log = log_widget

    def generate_username(self) -> str:
        letter = random.choice(string.ascii_lowercase)
        repeat_times = random.choice([3, 4])
        letters_part = letter * repeat_times
        digit_count = random.choice([2, 3])
        digits_part = ''.join(random.choices(string.digits, k=digit_count))
        return letters_part + digits_part

    def generate_password(self, min_length=8) -> str:
        digit_base = str(random.randint(10, 99))
        repeat_times = random.choice([3, 4])
        repeated_digits = digit_base * repeat_times
        letter_count = 1
        letters = ''.join(random.choices(string.ascii_lowercase, k=letter_count))
        password = repeated_digits + letters
        while len(password) < min_length:
            password += random.choice(string.ascii_lowercase)
        return password

    def get_email(self) -> Tuple[str, str, str]:
        """创建临时邮箱并返回 (email, password, token)"""
        try:
            # 获取域名
            domain_resp = requests.get("https://api.mail.tm/domains?page=1", verify=False, timeout=10)
            domain_data = domain_resp.json()
            if not domain_data.get('hydra:member'):
                raise Exception("邮箱服务返回空域名列表")
            domain = domain_data['hydra:member'][0]['domain']

            # 生成邮箱和密码
            email = f"{self.generate_username()}@{domain}"
            password = self.generate_password()

            # 创建账号
            create_resp = requests.post(
                "https://api.mail.tm/accounts",
                json={"address": email, "password": password},
                headers={'Content-Type': 'application/json'},
                verify=False,
                timeout=10
            )
            if create_resp.status_code not in [200, 201]:
                raise Exception(f"创建邮箱失败: {create_resp.text}")

            # 登录获取 token
            token_resp = requests.post(
                "https://api.mail.tm/token",
                json={"address": email, "password": password},
                headers={'Content-Type': 'application/json'},
                verify=False,
                timeout=10
            )
            if token_resp.status_code != 200:
                raise Exception(f"获取邮箱 token 失败: {token_resp.text}")

            token = token_resp.json()['token']
            self.log.debug("📧 邮箱创建成功: %s", email)
            self.log.debug("📧 邮箱密码: %s", password)
            return email, password, token

        except Exception as e:
            self.log.error("获取邮箱失败: %s", str(e))
            raise

    def extract_code(self, token: str) -> str:
        """从邮件中提取验证码"""
        for _ in range(10):  # 最多尝试 10 次
            time.sleep(5)
            try:
                resp = requests.get(
                    "https://api.mail.tm/messages?page=1",
                    headers={'Authorization': f'Bearer {token}'},
                    verify=False,
                    timeout=10
                )
                data = resp.json()
                for msg in data.get('hydra:member', []):
                    intro = msg.get('intro', '')
                    import re
                    codes = re.findall(r'\d{4}', intro)
                    if codes:
                        return codes[0]
            except Exception as e:
                self.log.error("检查邮件失败: %s", str(e))
        raise Exception("❌ 超时：未收到验证码邮件")

    def send_verification(self, email: str, type: int):
        url = f"{self.base_url}/account/rest/account/v1/verification"
        payload = {
            "email": email,
            "type": type,
            "key": "",
            "view": 0,
            "transaction": str(int(time.time() * 1000))
        }
        resp = requests.post(url, headers=self.headers, json=payload, verify=False)
        if resp.status_code != 200:
            raise Exception("发送验证码失败: %s", resp.text)

    def verify_code(self, email: str, code: str, type: int):
        url = f"{self.base_url}/app/v1/verification"
        payload = {
            "code": code,
            "email": email,
            "type": type,
            "key": "",
            "view": 0,
            "transaction": str(int(time.time() * 1000))
        }
        resp = requests.post(url, headers=self.headers, json=payload, verify=False)
        if resp.status_code != 200:
            raise Exception("验证码验证失败: %s", resp.text)

    def register(self, email: str, password: str, code: str):
        url = f"{self.base_url}/account/rest/account/v1/registry"
        payload = {
            "code": code,
            "email": email,
            "password": password,
            "key": "",
            "view": 0,
            "transaction": str(int(time.time() * 1000))
        }
        resp = requests.post(url, headers=self.headers, json=payload, verify=False)
        if resp.status_code != 200 or resp.json().status != 200:
            raise Exception("注册失败: %s", resp.text)

    def login(self, email: str, password: str):
        url = f"{self.base_url}/account/rest/account/v1/login"
        payload = {
            "client": "R28M61PLYNX",
            "email": email,
            "password": password,
            "key": "",
            "view": 0,
            "transaction": str(int(time.time() * 1000))
        }
        resp = requests.post(url, headers=self.headers, json=payload, verify=False)
        if resp.status_code != 200:
            raise Exception("登录失败: %s", resp.text)

    def generate_single_account(self) -> Dict[str, str]:
        """生成一个账号，返回 {'email': ..., 'password': ...}"""
        try:
            email, password, token = self.get_email()
            self.log.info("✅ 创建邮箱: %s", email)

            # 发送注册验证码 (type=3)
            self.send_verification(email, 3)
            self.log.debug("📨 已发送注册验证码...")
            code = self.extract_code(token)
            self.log.info("🔑 验证码: %s", code)

            # 验证验证码
            self.verify_code(email, code, 3)
            self.log.debug("✅ 验证码已验证")

            # 注册
            self.register(email, password, code)
            self.log.info("🎉 账号注册成功")

            # 登录（激活）
            self.login(email, password)
            self.log.debug("👤 账号已登录（激活）")

            # 发送 AID 验证码 (type=4)
            self.send_verification(email, 4)
            self.log.debug("📨 已发送 AID 验证码...")
            aid_code = self.extract_code(token)
            self.log.info("🔑 AID 验证码: %s", aid_code)
            self.verify_code(email, aid_code, 4)
            self.log.info("✅ AID 已激活")

            return {"email": email, "password": password}

        except Exception as e:
            self.log.error("生成账号失败: %s", str(e))
            raise

    def generate_accounts(self, count: int) -> List[Dict[str, str]]:
        """批量生成账号"""
        accounts = []
        delay_range = (2, 5)

        for i in range(count):
            self.log.info("🔄 开始生成第 %s/%s 个账号...", i + 1, count)
            try:
                account = self.generate_single_account()
                accounts.append(account)
                self.log.info("✅ 第 %s 个账号生成成功: ", i + 1)
                self.log.info("✅ email: %s ,password: %s ", account['email'], account['password'])
            except Exception as e:
                self.log.error("❌ 第 %s 个账号生成失败", i + 1)

            # 延迟（最后一个不延迟）
            if i < count - 1:
                delay = random.uniform(*delay_range)
                self.log.info("⏸️  等待 %.1f 秒...", delay)
                time.sleep(delay)

        return accounts
