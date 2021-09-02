from .database import db
from .api import API
import random

class API_High(API):
    def __init__(self, npsn: str, appver: str, ver: str, adid: str, countryname: str, devicename: str, deviceid: str, osname: str) -> None:
        super().__init__(npsn=npsn, appver=appver, ver=ver, adid=adid, countryname=countryname, devicename=devicename, deviceid=deviceid, osname=osname)
    
    def create_new_account(self):
        self.nexon_userinfo()
        self.masterlist()
        self.login()
        self.tutorial()

    def join_in(self, user_key: str, user_no:int, client_masterversion: str):
        self.user_key = user_key
        self.default_body["user_key"] = user_key
        self.default_body["client_masterversion"] = client_masterversion
        self.user_no = user_no
        

    def quest(self, quest_id: int):
        # typ prefix for battle and event
        quest_id = str(quest_id)
        typ = ""
        if quest_id in db.mainquest_stage:
            quest = db.mainquest_stage[quest_id]
            typ = "quest"
        elif quest_id in db.event_quest_stage:
            quest = db.event_quest_stage[quest_id]
            typ = "event"
        elif quest_id in db.huntingquest_stage:
            quest = db.huntingquest_stage[quest_id]
            typ = "hunting"
        print("clearing stage: ", quest_id, db.text[quest["title"]]["text_english"])
        wave_ids = []
        for i in range(1,99):
            wid = quest.get(f"wave_id{i}", None)
            if not wid:
                break
            wave_ids.append(wid)

        #party = self.partyinfo()["party"]
        if typ == "quest":
            battle = self.battlestart(quest_id)
        elif typ == "hunting":
            battle = self.battlehuntingstart(quest_id)
        else:
            raise NotImplementedError()
        # print chests [id, id, id]
        if battle["status"] != 0:
            return battle["status"]
        
        party = battle["party"]
        members = battle["members"]
        for i in range(len(wave_ids)-1):
            # [member_id,HP,position (1,2,3)]
            livemembers = [
                [member["id"],member["hp"],i+1]
                for i,member in enumerate(members)
                if member["exp"] 
            ]
            resume_info = {
                "resume_members" : [
                    {
                        "memberId": member["id"],
                        "spLevel": "%.2f" % (random.randint(0,100)/100),
                        "skill1Time": 0,
                        "skill2Time": 0,
                        "stateInfoArray": [],
                        "IsReserver": False
                    }
                    for i,member in enumerate(members)
                ]
            }
            self.battlewaveresult(i, livemembers, 1, resume_info)
        clearquestmission = [
            quest["mainmission"], quest["submission1"], quest["submission2"]
        ]
        if typ == "quest":
            res = self.result(quest_id, len(wave_ids), clearquestmission=clearquestmission)
        elif typ == "hunting":
            res = self.battlehuntingresult(quest_id, len(wave_ids), clearquestmission=clearquestmission)
        print(res)
        print("cleared")
        return #TODO