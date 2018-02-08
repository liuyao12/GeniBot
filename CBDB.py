import requests

fuxing = ['歐陽', '諸葛', '長孫', '万俟', '公孫', '夏侯', '慕容', '司馬', '司徒', '皇甫', '閭邱', '閭丘', '宇文', '上官', '范姜', '陸費', '耶律', '完顏', '侍其', '聞人', '獨孤', '尉遲']


class profile:
    def __init__(self, id):
        self.id = int(id)
        url = "https://cbdb.fas.harvard.edu/cbdbapi/person.php?id={}&o=json".format(str(id))
        r = requests.get(url)
        if r.json().get('Package', {}).get('PersonAuthority', {}).get('PersonInfo', '') == '':
            self.id = None
            return None
        data = r.json().get('Package', {}).get('PersonAuthority', {}).get('PersonInfo', {}).get('Person', {})
        self.rawdata = data

        bio = data.get('BasicInfo', {})
        self.dynasty = data.get('BasicInfo', {}).get('Dynasty', '')
        gender = bio.get('Gender', '0')
        if gender == '0':
            self.gender = "male"
        elif gender == '1':
            self.gender = "female"
        else:
            self.gender = "unknown"
        name = bio.get('ChName', '-')
        self.chName = name
        self.engName = bio.get('EngName', '').replace('v', 'ü')
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
            age = bio.get('YearsLived', '')
            if self.death.isdigit() and age.isdigit() and age != "0":
                self.birth = str(int(self.death) - int(age) + 1)
            else:
                self.birth = "?"

        zihao = ""
        if data.get('PersonAliases', {}) != "":
            aliases = data.get('PersonAliases', {}).get('Alias', [])
            if type(aliases) == dict:
                aliases = [aliases]
            for alias in aliases:
                zi = alias.get('AliasName', '')
                if alias.get('AliasType') in ['字', '號', '室名、別號', '未詳'] and zi not in zihao:
                    zihao = zihao + zi + ' '
            if len(zihao) > 1 and zihao[-1] == " ":
                zihao = zihao[:-1]
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
            addresses = data.get('PersonAddresses', {}).get('Address', [])
            if type(addresses) == dict:
                addresses = [addresses]
            jiguan = {}
            for address in addresses:
                if address['AddrType'] == '籍貫(基本地址)':
                    jiguan = address
                    break
            if jiguan == {} and len(addresses) > 0:
                jiguan = addresses[0]

            xian = jiguan.get('AddrName', '')
            if xian == '甄城':
                xian = '鄄城'

            if self.dynasty in ['明', '清', '民國']:
                zhou = jiguan.get('belongs2_name', '')
                if '省' in zhou:
                    zhou = zhou[:2]
            else:
                zhou = jiguan.get('belongs1_name', '')
                if '路' in zhou or '道' in zhou or '省' in zhou:
                    zhou = ''
                if len(zhou) > 2 and zhou[2] in ["府", "軍"]:
                    zhou = zhou[:2]

            if zhou == xian:
                self.natal = xian
            else:
                self.natal = zhou + xian
            if self.natal == '[未詳]':
                self.natal = ''
            if self.natal != "":
                self.natalFullname = '【{}】'.format(self.natal) + " " + self.fullname

        notes = bio.get("Notes", "")
        self.notes = "[https://cbdb.fas.harvard.edu/cbdbapi/person.php?id={} '''{}''' {}] ".format(str(self.id), self.engName, self.chName) + notes
        if len(notes.split(' ')) > 2:
            first2words = " ".join(notes.split(" ")[:2])
            name_in_notes = " ".join([word.split("(")[0] for word in first2words.split(" ")])
            if self.engName == name_in_notes:
                self.notes = "[https://cbdb.fas.harvard.edu/cbdbapi/person.php?id={} '''{}''' {}]".format(str(self.id), self.engName, self.chName) + notes[len(first2words):]

        if data.get('PersonKinshipInfo', '') == '':
            self.kins = []
        else:
            kins = data.get('PersonKinshipInfo', {}).get('Kinship', [])
            if type(kins) == dict:
                kins = [kins]
            self.kins = []
            for kin in kins:
                self.kins.append({'kin': kin.get('KinRel'), 'id': kin.get('KinPersonId'), 'name': kin.get('KinPersonName')})

        # data to add to Geni
        self.data = {"gender": self.gender,
                     "living": False,
                     "public": True,
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
