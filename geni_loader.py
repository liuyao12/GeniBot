import geni_api as geni
from pprint import pprint
import requests
import json
import CBDB
import webbrowser

# https://www.geni.com/platform/oauth/authorize?client_id=382&redirect_uri=www.geni.com&response_type=token

access_token = "XqZRaCljdW1ju9c0B81BMunAGkPwnuatVnAibH5S"  # Geni account for CBDB
immediate_family = ['F', 'S', 'S1', 'S2', 'S3', 'S4']


def print_basics(id):
    p = CBDB.profile(id)
    # geni.add_to_project(6000000072711396093, 46406)

    if p.id != None:
        print(p.fullname, p.birth + "-" + p.death, p.natal, p.id)
        pprint(p.kins)
        print(p.notes)
    else:
        print("id does not exist")


print_basics(4)

log = []


def make_tree(id, rel='', level=0):
    if level > max:
        return None
    p = CBDB.profile(id)
    if str(id) not in log:
        print('\t' * level, rel, p.natalFullname, "({}-{})".format(p.birth, p.death), p.id)
        log.append(str(id))
        for kin in p.kins:
            if kin['kin'] in immediate_family:
                make_tree(kin['id'], kin['kin'], level + 1)


ids = dict()


def add_tree(id, rel='', guid=None, level=0):
    if level > max:
        return None
    p = CBDB.profile(id)
    if str(id) not in log:
        print('\t' * level, rel, p.natalFullname, "({}-{})".format(p.birth, p.death))
        data = p.data
        if rel == '':
            guid = geni.add_profile(data)
        elif rel == 'F':
            guid = geni.add_profile(data, guid, 'parent')
        else:
            if len(rel) == 2 and rel[1].isdigit():
                data['names']['zh-TW']['suffix'] = order(rel[1])
            guid = geni.add_profile(data, guid, 'child')
        geni.add_to_project(guid, 46406)
        print('\t' * level, 'added ' + str(id) + ' to Geni: ' + str(guid))
        ids[p.id] = guid
        log.append(str(id))

        kins = p.kins
        for kin in p.kins:
            if kin['kin'] in immediate_family:
                add_tree(kin['id'], kin['kin'], guid, level + 1)
    return guid


id = 4

p = CBDB.profile(id)
print(geni.add_profile(p.data))

print(ids)
max = 5
make_tree(id)
# guid = add_tree(4)
# webbrowser.open('https://www.geni.com/family-tree/index/' + str(guid))


with open('CBDB2Geni.json', 'r+') as f:
    data = json.load(f)
    pprint(data)
    f.seek(0)
    for id in ids:
        data['dictionary'][id] == ids[id]
    json.dump(data, f, indent=3)
