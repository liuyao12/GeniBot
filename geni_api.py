import requests
import json
from pprint import pprint
from operator import itemgetter

# get access token from Geni API explorer https://www.geni.com/platform/developer/api_explorer
# or https://www.geni.com/platform/oauth/authorize?client_id=382&redirect_uri=www.geni.com&response_type=token
access_token = "REDACTED"
print("Access token: " + access_token)


def validate(access_token):
    # Validate access token
    r = requests.get("https://www.geni.com/platform/oauth/validate_token?access_token={}".format(access_token))
    print(r.json())
    return r.json().get('result', '') == 'OK'


validate(access_token)

# AC = {}

fuxing = ["歐陽", "諸葛", "長孫", "慕容", "司馬", "司徒", "皇甫", "閭丘", "宇文", "上官", "范姜", "陸費"]


def isEnglish(s):
    try:
        s.encode(encoding='utf-8').decode('ascii')
    except UnicodeDecodeError:
        return False
    else:
        return True


def stripId(url):  # get node id from url (not guid)
    url = url.split(" ")[0]
    if "profile-" in url:
        id = int(url.split("-")[1])
    else:
        id = -1
    return(id)


class profile:
    def __init__(self, id, type="g"):  # type = "g" or ""
        url = "https://www.geni.com/api/profile-{}{}".format(type, str(id))
        r = requests.get(url, data=AC)
        data = r.json()
        self.id = stripId(data["id"])

        self.fulldata = data  # raw data
        data.pop("mugshot_urls", None)
        data.pop("photo_urls", None)
        self.data = data
        self.names = {key: data.get(key, "") for key in ["first_name", "middle_name", "last_name", "maiden_name", "display_name", "title", "suffix"]}

    def nameLifespan(self):
        birth = self.data.get("birth", {}).get("date", {}).get("year", "?")
        death = self.data.get("death", {}).get("date", {}).get("year", "?")
        if self.data.get("is_alive", ""):
            death = ""
        if birth == "?" and death == "?":
            return self.data.get("name", "")
        else:
            return self.data.get("name", "") + " ({}—{})".format(str(birth), str(death))

    def parent(self, gender="male", type="birth"):
        unions = self.data.get("unions")
        for union in unions:
            r = requests.get(union, json=AC).json()
            if (type in ["birth", "biological"] and self.data["url"] in r.get("children", []) and self.data["url"] not in r.get("adopted_children", [])) or (type == "adopted" and self.data["url"] in r.get("adopted_children", [])):
                for url in r.get("partners", {}):
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

    def ancestry(self, forest=None, gender="male", type="birth"):
        p = self
        if forest == None:
            forest = []
        lineage = {"id": p.id, "name": p.nameLifespan(), "offs": []}
        print("Getting the ancestry of:", p.nameLifespan())
        i = 1
        while addAncestorToForest(lineage, forest) == False:
            p = p.parent(gender=gender, type=type)
            if p == None:
                forest.append(lineage)
                return forest
            else:
                print("G" + str(i) + ": " + p.nameLifespan())
                lineage = {"id": p.id, "name": p.nameLifespan(), "offs": [lineage]}
            i = i + 1
        return p.data.get("id", "no name")

    def fix(p, indent=0):  # customized fix
        language = "zh-TW"

        if "names" in p.data:
            return

        names = p.names
        names.pop("suffix")
        names.pop("title")

        if isEnglish(p.data.get("name", "")):
            # names = p.data.get("names", {}).get(language, {})
            for key in names:
                name = names[key]
                if name[:2] == "Mc" or name[:3] == "Mac":
                    name = name[:3].upper() + name[3:]
                if name == name.lower() or name == name.upper():
                    names[key] = normalCase(name)
            data = names
        else:
            fn = names.get("first_name", "")
            ln = names.get("last_name", "")
            mn = names.get("maiden_name", "")
            dn = names.get("display_name", "")
            aka = names.get("nicknames", "")
            middle = names.get("middle_name", "")
            names["display_name"] = ""
            names["maiden_name"] = ""
            if aka != "":
                names["middle_name"] = middle + " " + " ".join(aka.split(","))

            ln_e = ""
            if " " in ln:
                if isEnglish(ln.split(" ")[0]) == False and isEnglish(ln.split(" ")[1]):
                    ln_e = ln.split(" ")[1]
                    ln = ln.split(" ")[0]
                    names["last_name"] = ln

            if fn in [" ", "?", "？", "NN", "N.N.", "氏"]:
                names["first_name"] = ""
            else:
                if len(ln) > 1 and ln not in fuxing and len(fn) > 1 and mn == "":  # Manchu
                    names["maiden_name"] = names["last_name"].split(" ")[0]
                    names["last_name"] = names["first_name"][0]
                    names["first_name"] = names["first_name"][1:]

            prefix = dn.split(" ")[0]
            if fn not in prefix and ln not in prefix:
                names["title"] = prefix

            if "(" in dn and ")" in dn:
                names["suffix"] = dn.split("(")[1].split(")")[0]

            data = {
                "first_name": "",
                "middle_name": "",
                "last_name": ln_e,
                "maiden_name": "",
                "names": {
                    language: names
                }}

        url = "https://www.geni.com/api/profile-" + str(p.id) + "/update?access_token=" + access_token
        r = requests.post(url, json=data)
        print("  " * indent + "fixing", r.json().get("name", ""), r.json().get("id", "No id"))


def im_family(id, type="g"):
    url = "https://www.geni.com/api/profile-" + type + str(id) + "/immediate-family?fields=name&id"
    r = requests.get(url, json=AC)

    data = r.json().get("nodes", {})
    if type == "g":
        focus_id = stripId(data.get("id", ""))
    else:
        focus_id = id
    results = {key: data[key] for key in data if "profile-" in key and stripId(key) != focus_id}
    return results


def normalCase(name):
    if isEnglish(name) == False:
        return name
    if len(name) < 2:
        name = name.upper()
    else:
        name = name[0].upper() + name[1:].lower()
        for i in range(len(name) - 1):
            if name[i] in [" ", "-", ",", ".", "/", "'", '"', "(", "["] and name[i + 1] != " ":
                if i + 2 == len(name):
                    name = name[:i + 1] + name[i + 1].upper()
                else:
                    name = name[:i + 1] + name[i + 1].upper() + name[i + 2:]
        for prefix in ["Mc", "Mac", "O'", "Fitz"]:
            l = len(prefix)
            n = name.find(prefix)
            if n != -1 and n + l < len(name):
                name = name[:n + l] + name[n + l].upper() + name[n + l + 1:]

        for particle in ["Ab ", "Ap ", "Verch ", "Ferch ", "Ingen ", "Mac ", "Fitz ", "Des ", "Di ", "Du ", "Degli ", "Del ", "Della ", "Dit ", "Den ", "Ten ", "Van ", "Der ", "Ou ", "Von ", "Of ", "Or ", "The ", "Et ", "And ", "D'", "Comte ", "Duc ", "Seigneur ", "Mac ", "Nan ", "Sur-", "Y "]:
            if particle in name:
                name = name.replace(particle, particle.lower())

        for roman in ["Iii", "Ii", "Iv", "Viii", "Vii", "Vi", "Ix", "Xiii", "Xii", "Xi", "Xiv", "Xviii", "Xvii", "Xvi", "Xv", "Nn", "Fnu", "Lnu", "Mnu"]:
            if roman + " " in name + " " or roman + ")" in name:
                name = name.replace(roman, roman.upper())

        exceptions = {"Dewitt": "DeWitt", "Vandenbergh": "VanDenBergh", "Teneyck": "TenEyck", "Vancamp": "VanCamp", "Vancampen": "VanCampen", "Vanatter": "VanAtter", "Vanetten": "VanEtten", "Vandeusen": "VanDeusen", "Demuller": "DeMuller", "Vandusen": "VanDusen", "Vandeursen": "VanDeursen", "Delong": "DeLong", "Delonge": "DeLonge", "Demott": "DeMott", "Vanwinkle": "VanWinkle", "Vanantwerp": "VanAntwerp", "Dubois": "DuBois", "Degraff": "DeGraff", "MacK": "Mack", "MacAulay": "Macaulay", "van der Mark": "Van Der Mark", "FitzPatrick": "Fitzpatrick", "MacOmber": "Macomber"}
        for key in exceptions:
            if key + " " in name + " ":
                name = name.replace(key, exceptions[key])
    return name


s = "joHN 'Johnny/john' Xi of Violet A DOE-WEED-wer de Bary e.t. XViii"
print(s)
print(normalCase(s))


class Chinese(profile):
    def __init__(self, id, type="g"):
        super().__init__(self, id, type)

        if "zh-TW" not in self.data.get("names", {}) and "zh-CN" not in self.data.get("names", {}):
            return self.fullname

        lang = "zh-TW"
        if "zh-TW" not in self.data.get("names", {}) and "zh-CN" in self.data.get("names", {}):
            lang = "zh-CN"

        self.names = self.data.get("names", {}).get(lang, {})
        self.fullname = fullChineseName()

    def fullChineseName(self, surname=None, natal=None):  # construct display name

        fn = self.names.get("first_name", "")
        ln = self.data.get("names", {}).get(lang, {}).get("last_name", "")
        if ln == surname:  # hide surname
            ln = ""
        aka = self.data.get("names", {}).get(lang, {}).get("middle_name", "")
        if aka != "":
            aka = " (" + aka + ")"
        mn = self.data.get("names", {}).get(lang, {}).get("maiden_name", "")
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
        return fullname


fixed = []


def recursion(focus, max=5, level=0, tolerance=0, log=[]):
    if len(fixed) > 100000 or level > 300 or tolerance > max:
        return log

    if type(focus) == profile:
        family = im_family(focus.id, "")
    elif type(focus) == int:
        family = im_family(focus, "")
    else:
        print("Wrong input for focus")
        return log

    family = {key: family[key] for key in family if key not in fixed}

    if len(family) > 0:
        if type(focus) == profile:
            print("  " * level + "Level", level, "| Focus: " + focus.nameLifespan())
        else:
            print("  " * level + "Level", level, "| Focus: " + str(focus))
        second_pass = []  # criteria that need to access profile
        for key in family:
            # fn = p.data.get("names", {}).get("zh-TW", {}).get("first_name", "")
            # ln = p.data.get("names", {}).get("zh-TW", {}).get("last_name", "")
            # suffix = p.data.get("names", {}).get("zh-TW", {}).get("suffix", "")
            # creator = p.data.get("creator", "")
            # if creator in [
            #         "https://www.geni.com/api/user-5239929",
            #         "https://www.geni.com/api/user-4730491",
            #         "https://www.geni.com/api/user-1482071"]:
            name = family[key].get("name", "")
            if isEnglish(name) == True and normalCase(name) != name:  # and 'le ' in name:
                p = profile(key, "")
                if "curator" not in p.data and any([word == word.lower() or word == word.upper() for word in [p.names["first_name"], p.names["middle_name"], p.names["last_name"], p.names["maiden_name"]] if len(word) > 2]):  # criterion
                    p.fix(indent=level + 1)
                    second_pass.append(p)
            else:
                second_pass.append(stripId(key))
            fixed.append(key)
        print("  " * (level + 1) + "Total # fixed =", len(fixed))
        log.append([len(fixed), level])
        for p in second_pass:
            if type(p) == profile:
                log = recursion(p, max, level + 1, tolerance=0, log=log)
            elif type(p) == int:
                log = recursion(p, max, level + 1, tolerance=tolerance + 1, log=log)
    return log


def fixAll(id, type="g", max=5):
    p = profile(id, type)
    p.fix()
    log = recursion(p, max)
    print("Done! Total # of Profiles =", len(fixed))
    return log


def add_profile(data, guid=None, rel=None):
    if guid is None or rel is None:  # create a branch
        url = 'https://www.geni.com/api/profile/add?access_token=' + access_token
    else:  # add profile as guid's rel
        url = 'https://www.geni.com/api/profile-g{}/add-{}?access_token='.format(str(guid), rel) + access_token
    r = requests.post(url, data)
    print(r.json())
    id = r.json().get('guid', 'error')
    if data.get('is_alive', True) is False:
        requests.post('https://www.geni.com/api/profile-g{}/update-basics?is_alive=False&access_token={}'.format(id, access_token))
    return id


def add_to_project(id, project_id):
    url = 'https://www.geni.com/api/project-{}/add_profiles?profile_ids=g{}&access_token={}'.format(str(project_id), str(id), access_token)
    r = requests.post(url)
    return 'results' in r.json()


def spanTree(id, max):
    fixed[:] = []
    p = profile(id)
    log = recursion(p, max=max, log=[])
    print("Done! Total # of Profiles =", len(fixed))
    return log
    # from bokeh.plotting import figure, output_file, show

    # output_file("lines.html")

    # plot = figure(title="Growth of spanning tree for " + p.nameLifespan(), x_axis_label='# of profiles found', y_axis_label='recursion depth')
    # colors = ["blue", "red", "green"]
    # for i in range(len(y)):
    #     plot.line(x[i], y[i], legend="up to " + str(limits[i]) + " steps", line_color=colors[i], line_width=2)
    # show(plot)
    # return [x, y]


def migrateNames(id, type="g", moved=[], target="zh-TW"):
    if len(moved) > 2000:
        return moved
    p = profile(id, type)
    if p.id in moved:
        return moved
    else:
        if p.moveName(target=target) == False:
            return moved
        else:
            moved.append(p.id)
            for key in p.family():
                migrateNames(stripId(key), "", moved=moved, target=target)
            return moved


def mass(surname, start=1, target="zh-CN"):
    for page in range(start, 100):
        url = "https://www.geni.com/api/surname-" + str(surname) + "/profiles&page=" + str(page)
        print(url)
        r = requests.get(url)
        if r.json().get("results") == []:
            break
        results = r.json().get("results", [])
        for person in results:
            if person.get("names") == None and surname in person.get("last_name") and person.get("creator", "") != "https://www.geni.com/api/user-1633384":
                print(person.get("name", "NA"))
                ls = migrateNames(stripId(person.get("id", "")), "", moved=[], target=target)
                print("No of profiles:", len(ls))


def makeForest(profiles):
    forest = []
    for p in profiles:
        p.ancestry(forest)
    return forest


def updateForest(forest, surname=None, natal=None):
    for tree in forest:
        p = profile(tree["id"], "")
        if p.data.get("names", {}).get("zh-TW") != None:
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


def hanziToNumeral(suffix):
    if isEnglish(suffix):
        return None
    index = ["一", "二", "三", "四", "五", "六", "七", "八", "九", "十", "十一", "十二", "十三", "十四", "十五", "十六", "十七", "十八", "十九", "二十", "二十一", "二十二", "二十三", "二十四", "二十五", "二十六", "二十七", "二十八", "二十九", "三十"].find(suffix)
    if index != -1:
        return index + 1


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
    while url != None and len(matches) < 500 and pagecount < 20:
        url = url + "&fields=id,name,birth,death&access_token=" + access_token
        r = requests.get(url)
        results = r.json().get("results", [])
        for res in results:
            # if birthyear == 0 or res.get("birth", {}).get("date", {}).get("year") == birthyear:
            #     if deathyear == 0 or res.get("death", {}).get("date", {}).get("year") == deathyear:
            #         matches.append(res)
            if any(word.upper() in res.get("name", "") for word in name.split(" ")):
                matches.append(res)
        url = r.json().get("next_page")
        pagecount += 1
    for res in matches:
        res["id"] = stripId(res["id"])
    return matches


# L = search("Convict Scarborough 1788")
# print(len(L))
# newL = []
# for item in L:
#     id = item["id"]
#     p = profile(id, "")
#     if "project-38645" not in p.data.get("project_ids", []):
#         newL.append(p.data["guid"])
# print(newL)


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
