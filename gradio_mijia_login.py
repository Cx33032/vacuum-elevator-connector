import os, time, json, requests
from urllib import parse
import qrcode
from PIL import Image

from mijiaAPI import mijiaLogin
from mijiaAPI.urls import qrURL

class LoginError(Exception):
    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message
        super().__init__(f'Error code: {code}, message: {message}')

class GradioMijiaLogin(mijiaLogin):
    def QRlogin(self) -> tuple:
        """
        login with QR code, but instead of printing in terminal,
        return (PIL.Image, auth_data)
        """
        data = self._get_index()
        location = data['location']
        location_parsed = parse.parse_qs(parse.urlparse(location).query)
        params = {
            '_qrsize': 240,
            'qs': data['qs'],
            'bizDeviceType': '',
            'callback': data['callback'],
            '_json': 'true',
            'theme': '',
            'sid': 'xiaomiio',
            'needTheme': 'false',
            'showActiveX': 'false',
            'serviceParam': location_parsed['serviceParam'][0],
            '_local': 'zh_CN',
            '_sign': data['_sign'],
            '_dc': str(int(time.time() * 1000)),
        }
        url = qrURL + '?' + parse.urlencode(params)
        ret = self.session.get(url)
        if ret.status_code != 200:
            raise LoginError(ret.status_code, f'Failed to get QR code URL, {ret.text}')
        ret_data = json.loads(ret.text[11:])
        if ret_data['code'] != 0:
            raise LoginError(ret_data['code'], ret_data['desc'])
        
        loginurl = ret_data['loginUrl']

        # ✅ 用 qrcode 库生成二维码图片 (PIL.Image)
        qr_img = qrcode.make(loginurl)

        # 等待用户扫码
        try:
            ret = self.session.get(ret_data['lp'], timeout=60, headers={'Connection': 'keep-alive'})
        except requests.exceptions.Timeout:
            raise LoginError(-1, 'Timeout, please try again')
        if ret.status_code != 200:
            raise LoginError(ret.status_code, f'Failed to wait for login, {ret.text}')
        ret_data = json.loads(ret.text[11:])
        if ret_data['code'] != 0:
            raise LoginError(ret_data['code'], ret_data['desc'])

        auth_data = {
            'userId': ret_data['userId'],
            'ssecurity': ret_data['ssecurity'],
            'deviceId': data['deviceId'],
        }
        ret = self.session.get(ret_data['location'])
        if ret.status_code != 200:
            raise LoginError(ret.status_code, f'Failed to get location, {ret.text}')
        cookies = self.session.cookies.get_dict()
        auth_data['serviceToken'] = cookies['serviceToken']
        self.auth_data = auth_data

        # ✅ 返回 (二维码图像, 授权信息)
        return qr_img, auth_data
    
    def generate_qr_code(self) -> tuple:
        """
        login with QR code, but instead of printing in terminal,
        return PIL.Image
        """
        data = self._get_index()
        location = data['location']
        location_parsed = parse.parse_qs(parse.urlparse(location).query)
        params = {
            '_qrsize': 240,
            'qs': data['qs'],
            'bizDeviceType': '',
            'callback': data['callback'],
            '_json': 'true',
            'theme': '',
            'sid': 'xiaomiio',
            'needTheme': 'false',
            'showActiveX': 'false',
            'serviceParam': location_parsed['serviceParam'][0],
            '_local': 'zh_CN',
            '_sign': data['_sign'],
            '_dc': str(int(time.time() * 1000)),
        }
        url = qrURL + '?' + parse.urlencode(params)
        ret = self.session.get(url)
        if ret.status_code != 200:
            raise LoginError(ret.status_code, f'Failed to get QR code URL, {ret.text}')
        ret_data = json.loads(ret.text[11:])
        if ret_data['code'] != 0:
            raise LoginError(ret_data['code'], ret_data['desc'])
        
        loginurl = ret_data['loginUrl']

        # ✅ 用 qrcode 库生成二维码图片 (PIL.Image)
        qr_img = qrcode.make(loginurl)
        
        qr_img = qr_img.get_image()  # 确保是 RGB 模式
        
        return qr_img, ret_data

    def get_auth(self, ret_data) -> dict:
        data = self._get_index()
        # 等待用户扫码
        try:
            ret = self.session.get(ret_data['lp'], timeout=60, headers={'Connection': 'keep-alive'})
        except requests.exceptions.Timeout:
            raise LoginError(-1, 'Timeout, please try again')
        if ret.status_code != 200:
            raise LoginError(ret.status_code, f'Failed to wait for login, {ret.text}')
        ret_data = json.loads(ret.text[11:])
        if ret_data['code'] != 0:
            raise LoginError(ret_data['code'], ret_data['desc'])

        auth_data = {
            'userId': ret_data['userId'],
            'ssecurity': ret_data['ssecurity'],
            'deviceId': data['deviceId'],
        }
        ret = self.session.get(ret_data['location'])
        if ret.status_code != 200:
            raise LoginError(ret.status_code, f'Failed to get location, {ret.text}')
        cookies = self.session.cookies.get_dict()
        auth_data['serviceToken'] = cookies['serviceToken']
        self.auth_data = auth_data
        
        return auth_data