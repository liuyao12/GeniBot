import geni_api as geni
from pprint import pprint

f = open("FRS8.txt", "r")

data = []
for line in f:
    if len(line) > 10:
        i = line.find("[[")
        j = line.find("]]")
        name = line[i + 2:j]
        if name.find("|") != -1:
            name = name[:name.find("|")]
        if name.find(" (") != -1:
            name = name[:name.find(" (")]
        if name.find(", ") != -1:
            name = name[:name.find(", ")]
        line = line[j:]
        if line.find(" – ") != -1:
            n = line.find(" – ")
            birth = line[n - 4:n]
            death = line[n + 3:]
            if birth.isdigit() == True and len(death) > 10:
                death = death[death.find(" ") + 1:]
                death = death[death.find(" ") + 1:]
                death = death[0:4]
                if death.isdigit() == True:
                    # print(birth, death, name)
                    data.append([name, birth, death])

print("Total number:", len(data))

for i in range(328, len(data)):
    triple = data[i]
    matches = geni.search(triple[0], int(triple[1]), int(triple[2]))
    print("Checking", i, ": No. of matches = ", len(matches))
    if len(matches) >= 1:
        for match in matches:
            profile = geni.profile(match.get("id"), "")
            if "project-14476" in profile.data.get("project_ids", []):
                print(i, triple[0], "matches with", profile.nameLifespan())
            else:
                print(i, triple[0], "matches with", profile.nameLifespan(), profile.data.get("guid", "Not found"))
