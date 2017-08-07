import requests
import json
from pprint import pprint
from operator import itemgetter

# get access token from Geni API explorer https://www.geni.com/platform/developer/api_explorer
access_token = "REDACTED"    # as a string (in quotes)
print("Access token: " + access_token)

# Validate access token
print(requests.get("https://www.geni.com/platform/oauth/validate_token?access_token=" + access_token).text)

fuxing = ["歐陽", "諸葛", "長孫", "慕容", "司馬", "皇甫", "閭丘", "宇文"]


class profile:
    def __init__(self, id, type="g"):
        url = "https://www.geni.com/api/profile-" + type + str(id) + "?access_token=" + access_token
        r = requests.get(url)
        data = r.json()
        if type == "g":
            self.guid = id
            self.id = stripId(data["id"])
        if type == "":
            self.id = id
            self.guid = int(data["guid"])

        self.fulldata = data  # raw data
        if "mugshot_urls" in data:
            data.pop("mugshot_urls")
        if "photo_urls" in data:
            data.pop("photo_urls")
        self.data = data
        # set Chinese preferences
        self.Chinese()

    def Chinese(self, surname=None, natal=None):  # construct display name
        fn = self.data.get("names", {}).get("zh-TW", {}).get("first_name", "")
        ln = self.data.get("names", {}).get("zh-TW", {}).get("last_name", "")
        if ln == surname:  # hide surname
            ln = ""
        aka = self.data.get("names", {}).get("zh-TW", {}).get("middle_name", "")
        if aka != "":
            aka = " (" + aka + ")"
        mn = self.data.get("names", {}).get("zh-TW", {}).get("maiden_name", "")
        if mn != "" and mn != natal:
            mn = "【" + mn + "】"
        suffix = self.data.get("names", {}).get("zh-TW", {}).get("suffix", "")
        if suffix != "":
            suffix = " (" + suffix + ")"
        title = self.data.get("names", {}).get("zh-TW", {}).get("title", "")
        if title != "" and mn == "":
            mn == " "
        fullname = title + mn + ln + fn + suffix + aka
        if fullname != " ":
            self.data["name"] = fullname

    def nameLifespan(self):
        birth = self.data.get("birth", {}).get("date", {}).get("year", "?")
        death = self.data.get("death", {}).get("date", {}).get("year", "?")
        if birth == "?" and death == "?":
            return self.data["name"]
        else:
            return self.data["name"] + " (" + str(birth) + "－" + str(death) + ")"

    def family(self):
        url = "https://www.geni.com/api/profile-" + str(self.id) + "/immediate-family?fields=name&access_token=" + access_token
        r = requests.get(url)
        results = {}
        for key in r.json().get("nodes", {}):
            if "profile-" in key and stripId(key) != self.id:
                results[key] = r.json().get("nodes", {}).get(key)
        return results

    def parent(self, gender="male", type="birth"):
        unions = self.data.get("unions")
        for union in unions:
            url = union + "?access_token=" + access_token
            r = requests.get(url).json()
            if (type == "birth" and self.data["url"] in r.get("children", []) and self.data["url"] not in r.get("adopted_children", [])) or (type == "adopted" and self.data["url"] in r.get("adopted_children", [])):
                for url in r.get("partners"):
                    id = stripId(url)
                    parent = profile(id, "")
                    if parent.data["gender"] == gender:
                        return parent
        return None

    def father(self, type="birth"):
        return self.parent("male", type=type)

    def mother(self, type="birth"):
        return self.parent("female", type=type)

    def ancestor(self, generation, gender="male", type="birth"):
        p = self
        for i in range(generation):
            p = p.parent(gender=gender, type=type)
            if p == None:
                return None
        return p

    def ancestry(self, forest=[], gender="male", type="birth"):
        lineage = {"id": self.id, "name": self.nameLifespan(), "offs": []}
        print("Getting ancestors of:", self.nameLifespan())
        p = self
        i = 1
        while addAncestorToForest(lineage, forest) == False:
            p = p.parent(gender=gender, type=type)
            if p == None:
                forest.append(lineage)
                return forest
            else:
                print(i, ": ", p.nameLifespan())
                lineage = {"id": p.id, "name": p.nameLifespan(), "offs": [lineage]}
            i = i + 1
        return p.data.get("id", "no name")

    def areRelated(self, id2):
        p1 = self
        p2 = profile(id2)
        tree = []
        p1.ancestry(tree)
        id = p2.ancestry(tree)

    def moveName(self):
        url = "https://www.geni.com/api/profile-" + str(self.id) + "/update?access_token=" + access_token
        if self.data.get("names") == None:
            fn = self.data.get("first_name", "")
            ln = self.data.get("last_name", "")
            if isEnglish(ln) and isEnglish(fn):
                return False
            if fn == "?":
                fn = ""
            fn_english = " ".join([x for x in fn.split() if isEnglish(x)])
            fn = " ".join([x for x in fn.split() if isEnglish(x) == False])
            ln_english = " ".join([x for x in ln.split() if isEnglish(x)])
            ln = " ".join([x for x in ln.split() if isEnglish(x) == False])

            mn = self.data.get("maiden_name", "")
            suffix = self.data.get("suffix", "")
            if fn == suffix:
                suffix = ""
            if isEnglish(suffix):
                suffix_english = suffix
            dn = self.data.get("display_name", "")
            aka = self.data.get("nicknames", "")
            aka_english = [x for x in aka if isEnglish(x)]
            aka = " ".join([x for x in aka if isEnglish(x) == False])
            title = ""
            if " " + ln + fn in dn or " " + fn in dn:
                title = dn[:dn.find(" ")]
            if "(" in dn:
                suffix = dn[dn.find("(") + 1: dn.find(")")]
            if len(ln) > 1 and ln not in fuxing:  # probably a Manchu surname
                if len(fn) > 1 and mn == "":
                    mn = ln
                    ln = fn[0]
                    fn = fn[1:]
            data = {"names": {"en-US": {"first_name": fn_english, "last_name": ln_english, "maiden_name": "", "suffix": "", "display_name": ""}, "zh-TW": {"first_name": fn, "last_name": ln, "maiden_name": mn, "suffix": suffix, "title": title, "display_name": dn, "middle_name": aka}}}
            r = requests.post(url, json=data)
            print("migrating", r.json().get("name", "no name"), r.json().get("id", ""))
            return True
        else:
            if self.data.get("names", {}).get("en-US") == self.data.get("names", {}).get("zh-TW"):
                data = {"names": {"en-US": {"first_name": "", "last_name": "", "maiden_name": "", "suffix": "", "display_name": ""}}}
                r = requests.post(url, json=data)
                print("cleared English(default)", r.json().get("name", "No Name"))
                return True
        return False


def migrateNames(id, type="g", moved=[]):
    if len(moved) > 2000:
        return moved
    p = profile(id, type)
    if p.id in moved:
        return moved
    else:
        if p.moveName() == False:
            return moved
        else:
            moved.append(p.id)
            for key in p.family():
                migrateNames(stripId(key), "", moved)
            return moved


def makeForest(profiles):
    forest = []
    for p in profiles:
        p.ancestry(forest)
    return forest


def updateForest(forest, surname=None, natal=None):
    for tree in forest:
        p = profile(tree["id"], "")
        p.Chinese(surname=surname, natal=natal)
        tree["name"] = p.nameLifespan()
        updateForest(tree.get("offs"), surname=surname, natal=natal)
        suffix = p.data.get("names", {}).get("zh-TW", {}).get("suffix")
        max = 0
        if suffix != None:
            if suffix.find(".") != -1:
                suffix = suffix[:suffix.find(".")]
            num = hanziToNumeral(suffix)
            if num != None:
                tree["birthorder"] = num
                if num > max:
                    max = num
    for tree in forest:
        if tree.get("birthorder") == None:
            tree["birthorder"] = max + 1

    forest.sort(key=itemgetter("birthorder"))
    for tree in forest:
        tree.pop("birthorder")


def stripId(url):  # get node id from url (not guid)
    return(int(url[url.find("profile-") + 8:]))


def hanziToNumeral(suffix):
    if isEnglish(suffix):
        return None
    index = ["一", "二", "三", "四", "五", "六", "七", "八", "九", "十", "十一", "十二", "十三", "十四", "十五", "十六", "十七", "十八", "十九", "二十", "二十一", "二十二", "二十三", "二十四", "二十五", "二十六", "二十七", "二十八", "二十九", "三十"].find(suffix)
    if index != -1:
        return index + 1


def isEnglish(s):
    try:
        s.encode(encoding='utf-8').decode('ascii')
    except UnicodeDecodeError:
        return False
    else:
        return True


def addAncestorToForest(ancestor, forest):  # find if ancestor is in forest, and attach
    found = False
    i = 0
    while found == False and i < len(forest):
        tree = forest[i]
        if tree.get("id") == ancestor.get("id"):
            print("attaching " + ancestor.get("name"))
            tree.get("offs").extend(ancestor.get("offs"))
            found = True
        else:
            found = addAncestorToForest(ancestor, tree.get("offs"))
        i = i + 1
    return found


def project(id, max=2200):  # just the ids, into a list
    url = "https://www.geni.com/api/project-" + str(id) + "/profiles?fields=id,name,last_name,maiden_name&access_token=" + access_token
    print("Reading: ", url)
    r = requests.get(url).json()
    data = r.get("results")
    while r.get("next_page") != None and len(data) < max:
        print("Reading: ", r["next_page"])
        url = r["next_page"] + "&access_token=" + access_token
        r = requests.get(url).json()
        data = data + r["results"]
    return data


def countProjects(data):
    counts = {}
    for result in data:
        id = stripId(result["id"])
        p = profile(id, "")
        for project in p.data.get("project_ids", []):
            if project in counts:
                counts[project] += 1
            else:
                counts[project] = 1
    return counts


def search(name, birthyear=0, deathyear=0):
    url = "https://www.geni.com/api/profile/search?names=" + name
    matches = []
    pagecount = 0
    while url != None and len(matches) < 5 and pagecount < 10:
        url = url + "&fields=id,name,birth,death&access_token=" + access_token
        r = requests.get(url)
        results = r.json().get("results", [])
        for person in results:
            if birthyear == 0 or person.get("birth", {}).get("date", {}).get("year") == birthyear:
                if deathyear == 0 or person.get("death", {}).get("date", {}).get("year") == deathyear:
                    matches.append(person)
        url = r.json().get("next_page")
        pagecount += 1
    for match in matches:
        match["id"] = stripId(match["id"])
    return matches


def countSurname(profiles):
    counts = {"no name": 0}
    for p in profiles:
        surname = p.data.get("last_name")
        if surname == None:
            counts["no name"] += 1
        else:
            surnameZh = p.data.get("names", {}).get("zh-TW", {}).get("last_name")
            if surnameZh != surname:
                surname = surnameZh
            if surname in counts:
                counts[surname] += 1
            else:
                counts[surname] = 1
    return counts


def countNatal(profiles):
    counts = {"no natal": 0}
    for p in profiles:
        natal = p.data.get("names", {}).get("zh-TW", {}).get("maiden_name")
        if natal == None:
            counts["no natal"] += 1
        else:
            if natal in counts:
                counts[natal] += 1
            else:
                counts[natal] = 1
    return counts
