from base64 import b64decode
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad, pad
from .jwt_helper import jwt_encode, jwt_decode
import binascii
import json
from requests import Session
from hashlib import md5
from copy import copy
from .crypto_values import aes_key, aes_iv, jwt_key

class API:
    api: str
    user_key: str
    user_no: str
    default_body: dict
    session: Session

    def __init__(
        self,
        api="https://web-prod-konosuba.nexon.com",
        npsn: str = "19820000006844268",
        appver: str = "1.4.2",
        ver: str = "00000001",
        adid: str = "74e380f5-f3b6-4d02-b35b-7fbc9cff7aae",  # uuid4
        countryname: str = "DE",
        devicename: str = "SM-A908N",
        deviceid: str = "74e380f5-f3b6-4d02-b35b-7fbc9cff7aae",  # uuid4
        osname: str = "Android OS 5.1.1 / API-22 (LMY49I/V9.5.3.0.LACCNFA)",
    ) -> None:
        self.api = api
        self.user_key = None
        self.user_no = None
        self.session = Session()
        self.session.headers.update(
            {
                "Host": "web-prod-konosuba.nexon.com",
                "User-Agent": "UnityPlayer/2019.4.15f1 (UnityWebRequest/1.0, libcurl/7.52.0-DEV)",
                "Accept": "*/*",
                "Accept-Encoding": "deflate, gzip",
                "Content-Type": "application/octet-stream",
                "X-Unity-Version": "2019.4.15f1",
            }
        )
        self.default_body = {
            "npsn": npsn,
            "appver": appver,
            "ver": ver,
            "nexonsn": "",
            "adid": adid,
            "countryname": countryname,
            "devicename": devicename,
            "deviceid": deviceid,
            "osname": osname,
            "ostype": "A",
        }

    def request(self, path: str, body: dict):
        # 1. encrypt data
        data = self.encrypt_request_data(body) if body else None

        # 2. prepare application header
        payload = {"cs": binascii.hexlify(md5(data).digest()).decode()}
        if self.user_key:
            payload["uk"] = self.user_key

        app_header = jwt_encode(
            payload=payload,
            key=jwt_key,
        )
        self.session.headers["X-Application-Header"] = app_header

        # 3. send
        url = f"{self.api}{path}"
        if self.user_no:
            url += f"?u={self.user_no}"
        self.session.headers["Content-Length"] = str(len(data))
        res = self.session.post(url, data=data)

        # 4. decrypt
        data = self.decrypt_request_data(res)

        return json.loads(data)

    def decrypt_request_data(self, request):
        # iv
        iv = None
        app_header = request.headers.get("X-Application-Header", None)
        if app_header:
            # RSA, key ????
            payload = jwt_decode(app_header)

            if payload.get("uk", None):
                self.user_key = payload["uk"]
                print(self.user_key)
                # NetworkUtil_Hex2Bin(payload["uk"], 0x10)
                iv = binascii.unhexlify(payload["uk"])
                iv = b"\x00" * (0x10 - len(iv)) + iv

        if not iv:
            iv = aes_iv

        # key
        key = aes_key
        # res = NetworkUtil_Decrypt(request.content, key, iv)
        cipher = AES.new(key, AES.MODE_CBC, iv)
        decoded = cipher.decrypt(request.content)
        return unpad(decoded, 0x10, "pkcs7")

    def encrypt_request_data(self, body):
        data = "&".join("=".join(item) for item in body.items()).encode("utf8")

        # iv
        iv = None
        if self.user_key:
            iv = binascii.unhexlify(self.user_key)
            iv = b"\x00" * (0x10 - len(iv)) + iv
        else:
            iv = aes_iv
        # key
        key = aes_key

        # encode data
        cipher = AES.new(key, AES.MODE_CBC, iv)
        return cipher.encrypt(pad(data, 0x10, "pkcs7"))

    def nexon_userinfo(self, nptoken: str, npaCode: str):
        body = copy(self.default_body)
        body.update(
            {
                "nptoken": nptoken,
                "npaCode": npaCode,
                "platform_code": "2",
                "expired_date": "false",
                "client_masterversion": "-",
            }
        )
        ret = self.request("/api/nexon_userinfo", body)
        return ret

    def masterlist(self):
        body = copy(self.default_body)
        body.update(
            {
                "masterversion": "-",
                "client_masterversion": "-",
            }
        )
        ret = self.request("/api/masterlist", body)
        # set client_masterversion
        self.default_body["client_masterversion"] = ret["masterversion"]
        return ret

    def masterall(self, master_keys: list[str] = []):
        body = copy(self.default_body)
        body.update(
            {
                "masterversion": self.default_body["client_masterversion"],
                "master_keys": ",".join(master_keys),
                "client_masterversion": "-",
            }
        )
        ret = self.request("/api/masterall", body)
        # parse masterdata
        for entry in ret["masterarray"]:
            entry["master"] = json.loads(b64decode(entry["master"]))
        return ret

    def login(self, uuid: str, nptoken: str, npaCode: str):
        body = copy(self.default_body)
        body.update(
            {
                "uuid": uuid,
                "platform": "2",
                "rulever": "1",
                "advertising_id": "74e380f5-f3b6-4d02-b35b-7fbc9cff7aae",
                "nptoken": nptoken,
                "npaCode": npaCode,
                "userCountry": "DE276",
                "language": "EN",
                "loginPlatform": "9999",
                "os": body["osname"],
                "client_masterversion": "-",
            }
        )
        ret = self.request("/api/login", body)
        # set user key of instance and default body
        self.user_key = ret["user_key"]
        self.default_body["user_key"] = self.user_key
        self.user_no = ret["user_no"]
        # self.user_name = ret["user_name"]
        return ret

    def firebasetoken(self):
        body = copy(self.default_body)
        body.update(
            {
                "token": "c3TheW1iRGaZirM2eg7QHw:APA91bF8pbedLhJbrjN_rX17dDD-3-Y-QXd6p6UcPNdv-uCdebfv-F7fos-6MZTg3wnLnoS__-kPHMf6b5IuEyvuWJctTZZoYvSm4EB-Cjda2l_wSy1EA_r39Zq7Isnfob2u2Dew763T",
                "client_masterversion": "-",
            }
        )
        ret = self.request("/api/firebasetoken", body)
        return ret

    def tutorial(self):
        body = copy(self.default_body)
        body.update(
            {
                "type": "tutorial",
                "progress": "1",
            }
        )
        ret = self.request("/api/tutorial", body)
        return ret

    def notice(self):
        body = copy(self.default_body)
        ret = self.request("/api/notice", body)
        return ret

    def gachainfo(self):
        body = copy(self.default_body)
        ret = self.request("/api/gachainfo", body)
        return ret

    def root_box_check(self):
        body = copy(self.default_body)
        ret = self.request("/api/root_box_check", body)
        return ret

    def gachachain(self):
        body = copy(self.default_body)
        body.update(
            {
                "gacha_id": "100001",
                "money_type": "1",
            }
        )
        ret = self.request("/api/gachachain", body)
        return ret

    def setname(self):
        body = copy(self.default_body)
        body.update(
            {
                "name": "VzBsZg",
            }
        )
        ret = self.request("/api/setname", body)
        return ret

    def loginbonus(self):
        body = copy(self.default_body)
        ret = self.request("/api/loginbonus", body)
        return ret

    def maintenancecheck(self):
        body = copy(self.default_body)
        body.update(
            {
                "type": "1",
            }
        )
        ret = self.request("/api/maintenancecheck", body)
        return ret

    def presentlist(self):
        body = copy(self.default_body)
        body.update(
            {
                "start": "0",
                "end": "0",
                "language": "EN",
            }
        )
        ret = self.request("/api/presentlist", body)
        return ret

    def presentget(self, ids: list[str]):
        body = copy(self.default_body)
        body.update({"ids": ",".join(ids)})
        ret = self.request("/api/presentget", body)
        return ret

    def storyreward(self):
        body = copy(self.default_body)
        body.update(
            {
                "user_story_id": "3",
                "route": "direct",
            }
        )
        ret = self.request("/api/storyreward", body)
        return ret

    def gachaticket(self):
        body = copy(self.default_body)
        body.update(
            {
                "gacha_id": "200011",
            }
        )
        ret = self.request("/api/gachaticket", body)
        return ret

    def partyinfo(self):
        body = copy(self.default_body)
        ret = self.request("/api/partyinfo", body)
        return ret

    def partyoffer(self):
        body = copy(self.default_body)
        body.update(
            {
                "party_no": "1",
                "elemental": "none",
                "main": "1",
                "sub": "1",
                "equip": "1",
            }
        )
        ret = self.request("/api/partyoffer", body)
        return ret

    def partychangelist(self):
        body = copy(self.default_body)
        body.update(
            {
                "update_type": "member",
            }
        )
        ret = self.request("/api/partychangelist", body)
        return ret

    def partychange(self):
        body = copy(self.default_body)
        body.update(
            {
                "update_type": "main",
                "user_party_id": "8390881",
                "unique_id": "5",
            }
        )
        ret = self.request("/api/partychange", body)
        return ret

    def storylist(self):
        body = copy(self.default_body)
        body.update(
            {
                "type": "0",
            }
        )
        ret = self.request("/api/storylist", body)
        return ret

    def questmainarealist(self):
        body = copy(self.default_body)
        ret = self.request("/api/questmainarealist", body)
        return ret

    def questmainstagelist(self):
        body = copy(self.default_body)
        body.update(
            {
                "area_id": "1",
            }
        )
        ret = self.request("/api/questmainstagelist", body)
        return ret

    def battlestart(self, quest_id: int, party_no: int = 1):
        body = copy(self.default_body)
        body.update(
            {
                "quest_id": str(quest_id),
                "party_no": str(party_no),
            }
        )
        ret = self.request("/api/battlestart", body)
        ret["chest"] = list(map(int, ret["chest"].split(","))) if ret["chest"] else []
        return ret

    def battlehuntingstart(self, quest_id: int, party_no: int = 1):
        body = copy(self.default_body)
        body.update(
            {
                "quest_id": str(quest_id),
                "party_no": str(party_no),
            }
        )
        ret = self.request("/api/battlehuntingstart", body)
        ret["chest"] = list(map(int, ret["chest"].split(","))) if ret["chest"] else []
        return ret

    def battlewaveresult(
        self,
        wave: int,
        livemembers: list[list[int]],
        battletime: int,
        resume_info: dict,
    ):
        body = copy(self.default_body)
        body.update(
            {
                "wave": str(wave),
                "livemembers": f"""[{','.join(f"[{','.join(str(x) for x in member)}]" for member in livemembers)}]""",  # [[5,277,1],[30,192,2],[15,246,3]]",
                "battletime": str(battletime),
                "resume_info": json.dumps(resume_info, separators=(",", ":"))
                # "resume_info" : "{"resumeMembers":[{"memberId":1154100,"spLevel":0.20000000298023225,"skill1Time":0,"skill2Time":0,"stateInfoArray":[],"IsReserver":false},{"memberId":1134123,"spLevel":0.30000001192092898,"skill1Time":0,"skill2Time":0,"stateInfoArray":[],"IsReserver":false},{"memberId":1054100,"spLevel":0.3500000238418579,"skill1Time":17,"skill2Time":0,"stateInfoArray":[],"IsReserver":false}]}",
            }
        )
        ret = self.request("/api/battlewaveresult", body)
        return ret

    def result(
        self,
        quest_id: int,
        wave: int,
        party_no: int = 1,
        clearquestmission: list[int] = [],
        memchouckcount: int = 0,
        win: bool = True,
    ):
        body = copy(self.default_body)
        body.update(
            {
                "quest_id": str(quest_id),
                "party_no": str(party_no),
                "win": "1" if win else "0",
                "wave": str(wave),
                "clearquestmission": f"[{','.join(str(x) for x in clearquestmission)}]",
                "memcheckcount": str(memchouckcount),
            }
        )
        ret = self.request("/api/result", body)
        return ret

    def result(
        self,
        quest_id: int,
        wave: int,
        party_no: int = 1,
        clearquestmission: list[int] = [],
        memchouckcount: int = 0,
        win: bool = True,
    ):
        body = copy(self.default_body)
        body.update(
            {
                "quest_id": str(quest_id),
                "party_no": str(party_no),
                "win": "1" if win else "0",
                "wave": str(wave),
                "clearquestmission": f"[{','.join(str(x) for x in clearquestmission)}]",
                "memcheckcount": str(memchouckcount),
            }
        )
        ret = self.request("/api/result", body)
        return ret

    def battlehuntingresult(
        self,
        quest_id: int,
        wave: int,
        party_no: int = 1,
        clearquestmission: list[int] = [],
        memchouckcount: int = 0,
        win: bool = True,
    ):
        body = copy(self.default_body)
        body.update(
            {
                "quest_id": str(quest_id),
                "party_no": str(party_no),
                "win": "1" if win else "0",
                "wave": str(wave),
                "clearquestmission": f"[{','.join(str(x) for x in clearquestmission)}]",
                "memcheckcount": str(memchouckcount),
            }
        )
        ret = self.request("/api/battlehuntingresult", body)
        return ret

    def questhuntinglist(self):
        body = copy(self.default_body)
        ret = self.request("/api/questhuntinglist", body)
        return ret

    def mission(self):
        body = copy(self.default_body)
        body.update(
            {
                "type": "all",
            }
        )
        ret = self.request("/api/mission", body)
        return ret

    def missiongetall(self):
        body = copy(self.default_body)
        ret = self.request("/api/missiongetall", body)
        return ret

    def partymembers(self):
        body = copy(self.default_body)
        ret = self.request("/api/partymembers", body)
        return ret

    def gradeup(self):
        body = copy(self.default_body)
        body.update(
            {
                "user_member_id": "30",
                "num1": "6",
                "num2": "0",
                "num3": "5",
            }
        )
        ret = self.request("/api/gradeup", body)
        return ret

    def questhuntingstagelist(self):
        body = copy(self.default_body)
        body.update(
            {
                "area_id": "8",
            }
        )
        ret = self.request("/api/questhuntingstagelist", body)
        return ret

    def interaction(self):
        body = copy(self.default_body)
        ret = self.request("/api/interaction", body)
        return ret
