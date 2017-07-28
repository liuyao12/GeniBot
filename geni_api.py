import requests
import json
from pprint import pprint
from operator import itemgetter

# get access token from Geni API explorer
access_token = REDACTED
print("Access token: " + access_token)

# Validate access token
print(requests.get("https://www.geni.com/platform/oauth/validate_token?access_token=" + access_token).text)


def stripId(url):  # get node id from url (not guid)
    return(int(url[url.find("profile-") + 8:]))


class profile:
    def __init__(self, id, type="g"):  # id int or string
        url = "https://www.geni.com/api/profile-" + type + str(id) + "?access_token=" + access_token
        r = requests.get(url)
        data = r.json()
        suffix = data.get("names", {}).get("zh-TW", {}).get("suffix")

        if type == "g":
            self.guid = id
            self.id = stripId(data["id"])
        if type == "":
            self.id = id
            self.guid = int(data["guid"])

        if suffix != None:
            fullname = data["name"]
            index = fullname.find(" (")
            if index == -1:
                data["name"] = fullname + "(" + suffix + ")"
            else:
                data["name"] = fullname[:index] + "(" + suffix + ")" + fullname[index:]
        self.fulldata = data
        if "mugshot_urls" in data:
            data.pop("mugshot_urls")
        if "photo_urls" in data:
            data.pop("photo_urls")
        self.data = data

    def nameLifespan(self):
        birth = self.data.get("birth", {}).get("date", {}).get("year", "?")
        death = self.data.get("death", {}).get("date", {}).get("year", "?")
        if birth == "?" and death == "?":
            return self.data["name"]
        else:
            return self.data["name"] + " (" + str(birth) + " - " + str(death) + ")"

    def parent(self, gender="male"):
        unions = self.data.get("unions")
        for union in unions:
            url = union + "?access_token=" + access_token
            r = requests.get(url).json()
            if self.data["url"] in r.get("children"):
                for url in r.get("partners"):
                    id = stripId(url)
                    parent = profile(id, "")
                    if parent.data["gender"] == gender:
                        return parent
        return None

    def father(self):
        return self.parent("male")

    def mother(self):
        return self.parent("female")

    def ancestry(self, forest=[], gender="male"):
        lineage = {"id": self.id, "name": self.nameLifespan(), "offs": []}
        print("Getting ancestors of:", self.nameLifespan())
        person = self
        i = 1
        while addAncestorToForest(lineage, forest) == False:
            person = person.parent(gender)
            if person == None:
                forest.append(lineage)
                return forest
            else:
                print(i, ": ", person.nameLifespan())
                lineage = {"id": person.id, "name": person.nameLifespan(), "offs": [lineage]}
            i = i + 1
        return forest


def makeForest(profiles):
    forest = []
    for profile in profiles:
        profile.ancestry(forest)
    return forest


def updateForest(forest):
    for tree in forest:
        person = profile(tree["id"], "")
        tree["name"] = person.nameLifespan()
        updateForest(tree.get("offs"))
        suffix = person.data.get("names", {}).get("zh-TW", {}).get("suffix")
        if suffix == None:
            tree["birthorder"] = len(forest)
        else:
            if suffix.find(".") != -1:
                suffix = suffix[:suffix.find(".")]
            tree["birthorder"] = hanziToNumeral(suffix)
    forest.sort(key=itemgetter("birthorder"))
    for tree in forest:
        tree.pop("birthorder")


def hanziToNumeral(suffix):
    if suffix == "殤":
        return None
    if suffix == "一":
        return 1
    if suffix == "二":
        return 2
    if suffix == "三":
        return 3
    if suffix == "四":
        return 4
    if suffix == "五":
        return 5
    if suffix == "六":
        return 6
    if suffix == "七":
        return 7
    if suffix == "八":
        return 8
    if suffix == "九":
        return 9
    if suffix == "十":
        return 10
    else:
        if suffix[0] == "十":
            return 10 + hanziToNumeral(number[1])


def addAncestorToForest(ancestor, forest):  # find if ancestor is in forest, and attach
    found = False
    i = 0
    while found == False and i < len(forest):
        tree = forest[i]
        # print(tree.get("id"), " vs. ", ancestor.get("id"))
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


def countSurname(profiles):
    counts = {"no name": 0}
    for profile in profiles:
        surname = profile.data.get("last_name")
        if surname == None:
            counts["no name"] += 1
        else:
            surnameZh = profile.data.get("names", {}).get("zh-TW", {}).get("last_name")
            if surnameZh != surname:
                surname = surnameZh
            if surname in counts:
                counts[surname] += 1
            else:
                counts[surname] = 1
    return counts


def countNatal(profiles):
    counts = {"no natal": 0}
    for profile in profiles:
        natal = profile.data.get("names", {}).get("zh-TW", {}).get("maiden_name")
        if natal == None:
            counts["no natal"] += 1
        else:
            if natal in counts:
                counts[natal] += 1
            else:
                counts[natal] = 1
    return counts


# for person in lineage:
#     print(person["name"], lifespan(person))

# countProjects(profiles)

# countSurnames(profiles)

def search(name, birthyear=0, deathyear=0):  # list of triples (name, birthyear, deathyear)
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
