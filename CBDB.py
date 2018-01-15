import requests
import json
from pprint import pprint

fuxing = ["歐陽", "諸葛", "長孫", "慕容", "司馬", "司徒", "皇甫", "閭丘", "宇文", "上官", "范姜", "陸費"]
order = {str(i): ['', '一', '二', '三', '四', '五', '六', '七', '八', '九', '十'][i] for i in range(1, 11)}


class profile:
    def __init__(self, id):
        self.id = id
        url = "https://cbdb.fas.harvard.edu/cbdbapi/person.php?id={}&o=json".format(str(id))
        r = requests.get(url)
        if r.json().get('Package', {}).get('PersonAuthority', {}).get('PersonInfo', '') == '':
            self.id = None
            return None
        data = r.json().get('Package', {}).get('PersonAuthority', {}).get('PersonInfo', {}).get('Person', {})
        self.data = data

        bio = data.get('BasicInfo', {})
        gender = bio.get('gender', '0')
        if gender == '0':
            self.gender = "male"
        elif gender == '1':
            self.gender = "female"
        else:
            self.gender = "unknown"
        name = bio.get('ChName', '-')
        self.chName = name
        self.engName = bio.get('EngName', '')
        if "(" in self.engName:
            self.engName = " ".join([word.split("(")[0] for word in self.engName.split(" ")])
        if name[:2] in fuxing:
            self.ln = name[:2]
            self.fn = name[2:]
        else:
            self.ln = name[0]
            self.fn = name[1:]
        if self.fn != '':
            if self.fn[0] == '氏':
                self.fn = ''
        self.death = bio.get('YearDeath', '?')
        if self.death == '0' or not self.death.isdigit():
            self.death = "?"
        self.birth = bio.get('YearBirth', '?')
        if self.birth == '0' or not self.birth.isdigit():
            if self.death.isdigit() and bio.get("YearsLived", "").isdigit() and bio.get("YearsLived", "") != "0":
                self.birth = int(self.death) - int(bio.get('YearsLived', '')) + 1
            else:
                self.birth = "?"

        notes = bio.get("Notes", "")
        self.notes = notes  # modify to Geni style
        if len(notes) > 20:
            first2words = " ".join(notes.split(" ")[:2])
            name_in_notes = " ".join([word.split("(")[0] for word in first2words.split(" ")])
            if self.engName == name_in_notes:
                self.notes = "[https://cbdb.fas.harvard.edu/cbdbapi/person.php?id={} '''{}''' {}]".format(str(self.id), self.engName, self.chName) + notes[len(first2words):] + " — [https://www.geni.com/projects/CBDB-Hartwell-collection/46406 RMH]"
            else:
                self.notes = "[https://cbdb.fas.harvard.edu/cbdbapi/person.php?id={} '''{}''' {}]\n".format(str(self.id), self.engName, self.chName) + notes + " — [https://www.geni.com/projects/CBDB-Hartwell-collection/46406 RMH]"

        zihao = ""
        if data.get('PersonAliases', {}) != "":
            aliases = data.get('PersonAliases', {}).get('Alias', [])
            if type(aliases) == dict:
                aliases = [aliases]
            for alias in aliases:
                if alias.get('AliasType') in ["字", "號"] and alias.get('AliasName') not in zihao:
                    zihao = zihao + alias.get('AliasName', '') + " "
            if len(zihao) > 1 and zihao[len(zihao) - 1] == " ":
                zihao = zihao[:len(zihao) - 1]
        self.zihao = zihao

        if self.fn == '':
            self.fullname = self.ln + '氏'
        if zihao != '':
            self.fullname = "{} ({})".format(self.chName, zihao)
        else:
            self.fullname = self.chName

        self.natal = ''
        self.natalFullname = self.fullname
        if type(data.get('PersonAddresses', '')) != str:
            address = data.get('PersonAddresses', {}).get('Address', {})
            if type(address) == list:
                address = address[0]
            zhou = address.get('belongs1_name', '')
            if '路' in zhou:
                zhou = ''
            if len(zhou) > 2 and zhou[2] in ["府", "軍"]:
                zhou = zhou[:2]
            xian = address.get('AddrName', '')
            if zhou == xian:
                self.natal = xian
            else:
                self.natal = zhou + xian
            if self.natal == '[未詳]':
                self.natal = ''
            if self.natal != "":
                self.natalFullname = '【{}】'.format(self.natal) + " " + self.fullname

        if data.get('PersonKinshipInfo', '') == '':
            self.kins = []
        else:
            kins = data.get('PersonKinshipInfo', {}).get('Kinship', [])
            if type(kins) == dict:
                kins = [kins]
            self.kins = []
            for kin in kins:
                self.kins.append({'kin': kin.get('KinRel'), 'id': kin.get('KinPersonId'), 'name': kin.get('KinPersonName')})

        self.data = {"gender": self.gender,
                     "living": False,
                     "public": True,
                     "first_name": ' ',
                     "names": {
                         "en-US": {
                             "display_name": self.engName + " " + self.chName},
                         "zh-TW": {
                             "first_name": self.fn,
                             "last_name": self.ln,
                             "maiden_name": self.natal,
                             "middle_name": self.zihao}},
                     "about_me": self.notes}
        if self.birth.isdigit():
            self.data["birth"] = {"date": {"year": int(self.birth)}}
        if self.death.isdigit():
            self.data["death"] = {"date": {"year": int(self.death)}}
