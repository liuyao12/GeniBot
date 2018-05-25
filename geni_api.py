import requests
import json
from operator import itemgetter

# get access token from Geni API explorer https://www.geni.com/platform/developer/api_explorer
# or https://www.geni.com/platform/oauth/authorize?client_id=382&redirect_uri=www.geni.com&response_type=token
access_token = "REDACTED"
print("Access token: " + access_token)

AT = {'access_token': access_token}


def validate(token):
    # Validate access token
    AT = {'access_token': token}
    r = requests.get("https://www.geni.com/platform/oauth/validate_token", json=AT)
    print(r.json())
    return r.json().get('result', '') == 'OK'


validate(access_token)


fuxing = ['歐陽', '諸葛', '長孫', '万俟', '公孫', '夏侯', '慕容', '司馬', '司徒', '皇甫', '閭邱', '閭丘', '宇文', '上官', '范姜', '陸費', '耶律', '完顏', '侍其', '聞人', '獨孤', '尉遲']


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
    def __init__(self, id, id_type='g'):  # id_type = 'g' or ''
        url = 'https://www.geni.com/api/profile-{}{}'.format(id_type, str(id))
        r = requests.get(url, json=AT)
        data = r.json()
        while 'merged_into' in data:
            id = data['merged_into'].split('-')[1]
            url = "https://www.geni.com/api/profile-{}".format(str(id))
            r = requests.get(url, json=AT)
            data = r.json()
        self.id = stripId(data["id"])
        self.guid = data['guid']

        # url = 'https://www.geni.com/api/profile-{}?fields=about_me'.format(str(self.id))
        # r = requests.get(url, json=AT)
        # self.about_me = r.json().get('about_me', '')

        self.fulldata = data  # raw data
        data.pop("mugshot_urls", None)
        data.pop("photo_urls", None)
        self.data = data
        self.names = {key: data.get(key, "") for key in ["first_name", "middle_name", "last_name", "maiden_name", "display_name", "title", "suffix"]}

    def nameLifespan(self):
        birth = self.data.get("birth", {}).get("date", {}).get("year", "?")
        death = self.data.get("death", {}).get("date", {}).get("year", "?")
        if self.data.get("is_alive", False):
            death = " "
        if birth == "?" and death == "?":
            return self.data.get("name", "")
        else:
            return self.data.get("name", "") + " ({}—{})".format(str(birth), str(death))

    def parent(self, gender="male", birth_type="birth"):
        unions = self.data.get("unions")
        for union in unions:
            r = requests.get(union, json=AT).json()
            if (birth_type in ["birth", "biological"] and self.data["url"] in r.get("children", []) and self.data["url"] not in r.get("adopted_children", [])) or (birth_type == "adopted" and self.data["url"] in r.get("adopted_children", [])):
                for url in r.get("partners", {}):
                    id = stripId(url)
                    parent = profile(id, "")
                    if parent.data["gender"] == gender:
                        return parent
        return None

    def father(self, birth_type="birth"):
        return self.parent("male", birth_type=birth_type)

    def mother(self, birth_type="birth"):
        return self.parent("female", birth_type=birth_type)

    def ancestor(self, generation, gender="male", birth_type="birth"):
        p = self
        for i in range(generation):
            p = p.parent(gender=gender, birth_type=birth_type)
            if p is None:
                return None
        return p

    def ancestry(self, forest=None, gender="male", birth_type="birth"):
        p = self
        if forest is None:
            forest = []
        lineage = {"id": p.id, "name": p.nameLifespan(), "offs": []}
        print("Getting the ancestry of:", p.nameLifespan())
        i = 1
        while addAncestorToForest(lineage, forest) is False:
            p = p.parent(gender=gender, birth_type=birth_type)
            if p is None:
                forest.append(lineage)
                return forest
            else:
                print("G" + str(i) + ": " + p.nameLifespan())
                lineage = {"id": p.id, "name": p.nameLifespan(), "offs": [lineage]}
            i = i + 1
        return p.data.get("id", "no name")

    def update_about(self, text, gender=0):
        data = {'about_me': str(text)}
        if gender == 1:
            data['gender'] = 'female'
        url = 'https://www.geni.com/api/profile-{}/update-basics?access_token={}'.format(self.id, access_token)
        r = requests.post(url, json=data)

    def fix(p, indent=0):  # customized fix

        if isEnglish(p.data.get("name", "")):
            names = p.names
            data = dict()
            for key in ['first_name', 'middle_name', 'last_name', 'maiden_name']:
                name = names.get(key, '')
                if len(name) > 3:
                    if name[:2] == "Mc" or name[:3] == "Mac" or name[:2] == "De":
                        name = name[:3].upper() + name[3:]
                if name == name.lower() or name == name.upper():
                    new_name = normalCase(name)
                    if names.get(key, '') != new_name:
                        data[key] = new_name
            if len(data) > 0:
                for key in ['suffix', 'title', 'display_name']:
                    name = names.get(key, '')
                    if len(name) > 0:
                        if name == name.lower() or name == name.upper():
                            new_name = normalCase(name)
                            if names[key] != new_name:
                                data[key] = new_name
        else:
            language = "zh-TW"
            names = p.data.get('names', {}).get(language, {})
            fn = names.get("first_name", "")
            ln = names.get("last_name", "")
            mn = names.get("maiden_name", "")
            dn = names.get("display_name", "")
            aka = names.get("nicknames", "")
            middle = names.get("middle_name", "")
            if ln == '裴' and mn in ['絳州聞喜', '河南洛陽', '慶州']:
                data = {
                    # "first_name": '',
                    # # "middle_name": '',
                    # "last_name": '',
                    # "maiden_name": '',
                    # 'display_name': '',
                    "names": {
                        language: {
                            # 'first_name': fn,
                            # 'last_name': ln,
                            # 'display_name': dn
                            'maiden_name': '河東聞喜'
                        }
                    }
                }
            else:
                data = dict()
        if len(data) == 0:
            return False
        else:
            url = "https://www.geni.com/api/profile-" + str(p.id) + "/update?access_token=" + access_token
            r = requests.post(url, json=data)
            print("  " * indent + "fixing", r.json().get("name", ""), r.json().get("id", "No id"))
            return True


def im_family(id, id_type='g'):
    if id_type == 'g':
        id = profile(id, id_type).id
    url = 'https://www.geni.com/api/profile-{}/immediate-family?fields=name,guid'.format(str(id))
    r = requests.get(url, json=AT)
    data = r.json().get("nodes", {})
    results = {key: data[key] for key in data if 'profile-' in key and stripId(key) != id}
    return results


def normalCase(name):
    if not isEnglish(name):
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

        for particle in ["Ab ", "Ap ", "Verch ", "Ferch ", "Ingen ", "Mac ", "Fitz ", "De ", "Des ", "Di ", "Du ", "Degli ", "Del ", "Della ", "Dit ", "Den ", "Ten ", "Van ", "Der ", "Ou ", "Von ", "Of ", "Or ", "The ", "Et ", "And ", "D'", "Comte ", "Duc ", "Seigneur ", "Mac ", "Nan ", "Sur-", "Y "]:
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
    def __init__(self, id, id_type='g'):
        super().__init__(id, id_type)

        if "zh-TW" not in self.data.get('names', {}) and "zh-CN" not in self.data.get('names', {}):
            self.fullname = self.data.get('name', '')
        else:
            lang = "zh-TW"
            if "zh-TW" not in self.data.get("names", {}) and "zh-CN" in self.data.get("names", {}):
                lang = "zh-CN"

            names = self.data.get("names", {}).get(lang, {})
            fn = names.get("first_name", "氏")
            ln = names.get("last_name", "")
            aka = names.get("middle_name", "")
            mn = names.get("maiden_name", "")
            suffix = names.get("suffix", "")
            title = names.get("title", "")

            if aka != "":
                aka = " (" + aka + ")"
            if mn != "" and mn != ln:
                mn = "【" + mn + "】"
            if suffix != "":
                suffix = " (" + suffix + ")"
            if mn == '':
                self.fullname = title + ' ' + ln + fn + suffix + aka
            else:
                self.fullname = title + mn + ln + fn + suffix + aka


fixed = []


def recursion(focus, max=5, level=0, tolerance=0, log=[]):
    if len(fixed) > 100000 or level > 300 or tolerance > max:
        return log

    if type(focus) == profile:
        family = im_family(focus.id, '')
    elif type(focus) == int:
        family = im_family(focus, '')
    else:
        print("Wrong input for focus")
        return log

    if level == 0:
        family = {key: family[key] for key in family}
    else:
        family = {key: family[key] for key in family if key not in fixed}

    if len(family) > 0:
        if type(focus) == profile:
            print("  " * level + "Level", level, "| Focus: " + focus.nameLifespan())
        else:
            print("  " * level + "Level", level, "| Focus: " + str(focus))
        second_pass = []  # criteria that need to access profile
        for key in family:
            name = family[key].get("name", "")
            if isEnglish(name) is True:
                if any(word == word.upper() or word == word.lower() or word[:2] == 'Mc' or word[:3] == 'Mac' for word in name.split() if len(word) > 2 and word != 'III'):
                    p = profile(key, '')
                    # creator = p.data.get("creator", "")
                    # if creator in [
                    #         "https://www.geni.com/api/user-5239929",
                    #         "https://www.geni.com/api/user-4730491",
                    #         "https://www.geni.com/api/user-1482071"]:
                    if 'curator' not in p.data and p.fix(indent=level + 1):
                        second_pass.append(p)
                    else:
                        second_pass.append(p.id)
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


def fixAll(id, id_type="g", max=5):
    p = profile(id, id_type)
    p.fix()
    log = recursion(p, max)
    print("Done! Total # of Profiles =", len(fixed))
    return log


def add_profile(data, guid=None, rel=None):
    if guid is None or rel is None:  # create a branch
        url = 'https://www.geni.com/api/profile/add?access_token=' + access_token
    elif rel in ['parent', 'child', 'sibling']:  # add profile as guid's rel (parent/sibling/child)
        url = 'https://www.geni.com/api/profile-g{}/add-{}?access_token='.format(str(guid), rel) + access_token
    r = requests.post(url, json=data)
    guid = r.json().get('guid', 'error')
    return guid


def update(guid, data):
    url = 'https://www.geni.com/api/profile-g{}/update?access_token='.format(str(guid)) + access_token
    r = requests.post(url, json=data)


def add_to_project(guid, project_id):
    url = 'https://www.geni.com/api/project-{}/add_profiles?profile_ids=g{}&access_token={}'.format(str(project_id), str(guid), access_token)
    r = requests.post(url)
    return 'results' in r.json()


def tree_growth(id, id_type='g', max=5):
    if type(id) == int:
        if id_type == 'g':
            id = profile(id).id
        data = [[id]]
    elif type(id) == list:
        data = id
        max = len(data) + max
    while len(data) <= max:
        data.append([])
        for id in data[-2]:
            imf = [stripId(key) for key in im_family(id, id_type='')]
            flatten = [id for gen in data for id in gen]
            data[-1].extend([id for id in imf if id not in flatten])
        print('generation', len(data) - 1, ':', len(data[-1]), sum(len(x) for x in data))
    return data

    # fixed[:] = []
    # p = profile(id)
    # log = recursion(p, max=max, log=[])
    # print("Done! Total # of Profiles =", len(fixed))
    # return log
    # from bokeh.plotting import figure, output_file, show

    # output_file("lines.html")

    # plot = figure(title="Growth of spanning tree for " + p.nameLifespan(), x_axis_label='# of profiles found', y_axis_label='recursion depth')
    # colors = ["blue", "red", "green"]
    # for i in range(len(y)):
    #     plot.line(x[i], y[i], legend="up to " + str(limits[i]) + " steps", line_color=colors[i], line_width=2)
    # show(plot)
    # return [x, y]


def progeny(id, id_type='g', level=0):
    focus = Chinese(id, id_type)
    if focus.data.get('public', False) is False and focus.data.get('gender', '') in ['', 'male', 'female']:
        return None
    focus_id = 'https://www.geni.com/api/' + focus.data['id']
    tree = {'name': focus.fullname,
            'id': focus.guid,
            'gender': focus.data.get('gender', '')}
    print('   ' * level, focus.fullname)
    # if focus.data.get('gender') == femaile:
    #     return tree
    for union in focus.data['unions']:
        r = requests.get(union, json=AT)
        if focus_id in r.json().get('partners', []):
            if focus.data.get('gender', '') == 'male':
                for child in r.json().get('children', []):
                    child_tree = progeny(stripId(child), '', level=level + 1)
                    if child_tree is not None:
                        if 'children' not in tree:
                            tree['children'] = []
                        tree['children'].append(child_tree)
            if r.json().get('status', '') in ['spouse', 'ex_spouse']:
                for partner in r.json().get('partners', []):
                    if focus_id != partner:
                        spouse = Chinese(stripId(partner), '')
                        if 'spouse' in tree:
                            tree['spouse'] = tree['spouse'] + ' | ' + spouse.fullname
                        else:
                            tree['spouse'] = spouse.fullname
    tree['count'] = sum(child['count'] for child in tree.get('children', [])) + len(tree.get('children', []))
    print('   ' * level, tree['count'])
    if level == 0:
        print('DONE!')
        with open('AisinGioro2.json', 'w', encoding='utf-8') as f:
            json.dump(tree, f, indent=3)
    return tree


def update_progeny(tree={}, level=0):
    # if tree.get('id', '').isdigit():
    #     p = Chinese(tree['id'])
    #     if p.fullname != tree['name']:
    #         tree['name'] = p.fullname
    for child in tree.get('children', []):
        update_progeny(child, level=level + 1)
    count = sum(child['count'] for child in tree.get('children', [])) + len(tree.get('children', []))
    print('   ' * level, count)
    tree['count'] = count


def order_progeny(tree={}, path=[], order=None):
    for index in path:
        tree = tree['children'][index]
    if 'children' not in tree:
        return tree
    if order is None:
        order = []
        for child in tree['children']:
            if ' (' in child.get('name', ''):
                hang = hanziToNumeral(child['name'].split(' (')[1].split(')')[0].split('.')[0])
                order.append(hang)
            else:
                order.append(0)
    for i in range(1, 35):
        if i in order:
            tree['children'].append(tree['children'].pop(order.index(i)))
            order.append(order.pop(order.index(i)))
    return tree

# with open('Victoria.json', 'r+', encoding='utf-8') as f:
#     data = json.load(f)
#     with open('test.json', 'w') as g:
#         json.dump(data, g, indent=3)
#     update_progeny(data)
#     f.seek(0)
#     json.dump(data, f, indent=3)


def migrateNames(id, id_type="g", moved=[], target="zh-TW"):
    if len(moved) > 2000:
        return moved
    p = profile(id, id_type)
    if p.id in moved:
        return moved
    else:
        if p.moveName(target=target) is False:
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
            if person.get("names") is None and surname in person.get("last_name") and person.get("creator", "") != "https://www.geni.com/api/user-1633384":
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
        if p.data.get("names", {}).get("zh-TW") is not None:
            p.Chinese(surname=surname, natal=natal)
        tree["name"] = p.nameLifespan()
        updateForest(tree.get("offs"), surname=surname, natal=natal)
        suffix = p.data.get("names", {}).get("zh-TW", {}).get("suffix")
        max = 0
        if suffix is not None:
            if suffix.find(".") != -1:
                suffix = suffix[:suffix.find(".")]
            num = hanziToNumeral(suffix)
            if num is not None:
                tree["birthorder"] = num
                if num > max:
                    max = num
    for tree in forest:
        if tree.get("birthorder") is None:
            tree["birthorder"] = max + 1

    forest.sort(key=itemgetter("birthorder"))
    for tree in forest:
        tree.pop("birthorder")


def hanziToNumeral(suffix):
    if isEnglish(suffix):
        return None
    hangs = ['', "一", "二", "三", "四", "五", "六", "七", "八", "九", "十", "十一", "十二", "十三", "十四", "十五", "十六", "十七", "十八", "十九", "二十", "二十一", "二十二", "二十三", "二十四", "二十五", "二十六", "二十七", "二十八", "二十九", "三十"]
    if suffix in hangs:
        return hangs.index(suffix)
    else:
        return -1


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


def project(id, max=10000):  # just the ids, into a list
    url = 'https://www.geni.com/api/project-{}/profiles?fields=id,name,last_name,maiden_name,birth,death'.format(str(id))
    print("Reading: ", url)
    r = requests.get(url, json=AT).json()
    data = r.get("results")
    while r.get("next_page") is not None and len(data) < max:
        print("Reading: ", r["next_page"])
        url = r["next_page"] + "&access_token=" + access_token
        r = requests.get(url).json()
        data = data + r["results"]

    print(len(data))
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
    url = 'https://www.geni.com/api/profile/search?names=' + name
    matches = []
    pagecount = 0
    if type(birthyear) != int:
        birthyear = 0
    if type(deathyear) != int:
        deathyear = 0
    while url is not None and len(matches) < 10 and pagecount < 5:
        url = url + '&fields=profile_url,guid,name,birth,death'
        r = requests.get(url)
        results = r.json().get("results", [])
        for res in results:
            if birthyear == 0 or res.get("birth", {}).get("date", {}).get("year") == birthyear:
                if deathyear == 0 or res.get("death", {}).get("date", {}).get("year") == deathyear:
                    matches.append(res)
            if any(word.upper() in res.get("name", "") for word in name.split(" ")):
                matches.append(res)
        url = r.json().get("next_page")
        pagecount += 1
    return matches


def countSurname(profiles):
    counts = {"no name": 0}
    for p in profiles:
        surname = p.data.get("last_name")
        if surname is None:
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
        if natal is None:
            counts["no natal"] += 1
        else:
            if natal in counts:
                counts[natal] += 1
            else:
                counts[natal] = 1
    return counts
