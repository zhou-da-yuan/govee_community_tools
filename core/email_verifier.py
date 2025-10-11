# core/email_verifier.py
import re
import requests
import json
import logging
from utils.logger import SimpleLogger

# 禁用不安全请求警告
requests.packages.urllib3.disable_warnings(
    requests.packages.urllib3.exceptions.InsecureRequestWarning
)

class EmailVerifier:
    def __init__(self, base_url: str = "https://api.mail.tm", log=None):
        self.base_url = base_url
        self.auth_url = f"{self.base_url}/token"
        self.messages_url = f"{self.base_url}/messages?page=1"
        self.log = log or SimpleLogger(print)  # 默认输出到控制台

    def get_verification_code(self, email: str, password: str, code_length: int = 4) -> str:
        """
        登录 mail.tm 并获取最新邮件中的验证码
        :param email: 邮箱地址
        :param password: 邮箱密码
        :param code_length: 验证码位数，默认 4 位
        :return: 验证码字符串，未找到返回 None
        """
        self.log(f"📨 正在登录邮箱: {email}")

        # Step 1: 获取 Token
        try:
            payload = json.dumps({"address": email, "password": password})
            headers = {'Content-Type': 'application/json'}

            response = requests.post(
                self.auth_url,
                headers=headers,
                data=payload,
                verify=False,
                timeout=10
            )

            if response.status_code != 200:
                self.log(f"❌ 登录失败: {response.status_code} - {response.text}")
                return None

            token = response.json().get("token")
            if not token:
                self.log("❌ 未获取到 token")
                return None

            self.log("✅ 登录成功，正在获取邮件列表...")

            # Step 2: 获取最新邮件
            headers = {'Authorization': f'Bearer {token}'}
            response = requests.get(
                self.messages_url,
                headers=headers,
                verify=False,
                timeout=10
            )

            if response.status_code != 200:
                self.log(f"❌ 获取邮件失败: {response.status_code}")
                return None

            data = response.json()
            if not data.get("hydra:member"):
                self.log("📭 邮箱为空，无邮件")
                return None

            # 获取最新邮件的 intro 字段
            intro = data["hydra:member"][0]["intro"]
            self.log(f"📬 获取到最新邮件内容: {intro}")

            # 提取指定长度的数字验证码
            pattern = r'\b\d{' + str(code_length) + r'}\b'
            codes = re.findall(pattern, intro)

            if codes:
                code = codes[0]
                self.log(f"🎉 成功提取 {code_length} 位验证码: {code}")
                return code
            else:
                self.log(f"🔍 未在邮件中找到 {code_length} 位验证码")
                return None

        except Exception as e:
            self.log(f"🚨 获取验证码时发生异常: {str(e)}")
            return None