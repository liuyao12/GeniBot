import geni_api as geni
from pprint import pprint
import requests
import json
import CBDB
import webbrowser

# https://www.geni.com/platform/oauth/authorize?client_id=382&redirect_uri=www.geni.com&response_type=token

access_token = REDACTED  # Geni account for CBDB

sons = ['S' + str(i) for i in range(1, 14)]
daughters = ['D' + str(i) for i in range(1, 14)]
tongzong = sons + daughters + ['S', 'D', 'Sn', 'S (only son)', 'S (only surviving son)', 'S (eldest surviving son)']
order = ['', '一', '二', '三', '四', '五', '六', '七', '八', '九', '十', '十一', '十二', '十三']


with open('CBDB2Geni.json', 'r') as f:
    all_ids = json.load(f)
    all_ids = [key for key in all_ids]


def info(id):
    p = CBDB.profile(id)
    # geni.add_to_project(6000000072711396093, 46406)

    if p.id is not None:
        print(p.id, p.natalFullname, p.birth + "-" + p.death)
        pprint(p.kins)
        print(p.notes)
        # pprint(p.rawdata)
    else:
        print("id does not exist")


def draw_tree(id, rel='', level=0, log=[]):
    p = CBDB.profile(id)
    if p.id is None:
        return None
    if str(id) not in log:
        print('\t' * level, rel, p.natalFullname, "({}-{})".format(p.birth, p.death), p.id)
        log.append(str(id))
        if 'D' not in rel:
            for kin in p.kins:
                if kin['kin'] in tongzong and kin['id'] != '0':  # and kin['id'] not in all_ids:
                    draw_tree(kin['id'], kin['kin'], level + 1, log)


def recursion(id, rel='', focus_guid=None, level=0, log=[], sibling=None):
    if id in log:
        return None
    p = CBDB.profile(id)
    if p.id is None:
        return None
    print('\t' * level, len(log), p.natalFullname, "({}-{})".format(p.birth, p.death))
    data = p.data
    if rel == '':
        guid = geni.add_profile(data)
    elif rel == 'F':
        return  # guid = geni.add_profile(data, guid, 'parent')
    else:
        if len(rel) == 2 and rel[1].isdigit():
            data['names']['zh-TW']['suffix'] = order[int(rel[1])]
        if rel[0] == 'D':
            data['gender'] = 'female'
        if sibling is None:
            guid = geni.add_profile(data, focus_guid, 'child')
        else:
            guid = geni.add_profile(data, sibling, 'sibling')

    if guid == 'error':
        print('error when adding profile')
    else:
        log.append(id)
        with open('CBDB2Geni.json', 'r+') as f:
            data = json.load(f)
            f.seek(0)
            if str(id) not in data:
                data[str(id)] = int(guid)
                json.dump(data, f, indent=3)
            else:
                record_id = data[str(id)]
                record_id = geni.profile(record_id).guid
                webbrowser.open('https://www.geni.com/merge/merge?complete=1&ids={},{}'.format(str(guid), str(record_id)))
        if 'Tackett' in p.notes or 'NewEpitaphID' in p.notes:
            geni.add_to_project(guid, 47011)
        else:
            geni.add_to_project(guid, 46406)
        print('\t' * level, 'added ' + str(id) + ' to Geni as ' + str(guid))

    if rel == 'D':
        return guid
    sibling = None
    for kin in p.kins:
        if kin['kin'] in tongzong and kin['id'] not in all_ids and kin['id'] != '0':
            child_guid = recursion(kin['id'], kin['kin'], guid, level + 1, log, sibling=sibling)
            if sibling is None:
                sibling = child_guid
    sibling = None
    return guid


def add_tree(id):
    p = CBDB.profile(id)
    if p.id is None:
        print('invalid id', id)
        return None
    with open('CBDB2Geni.json', 'r') as f:
        data = json.load(f)
    if str(p.id) in data:
        print(id, p.natalFullname, 'already entered')
    else:
        if p.dynasty in ['明', '清']:
            #     print(id, p.natalFullname, p.dynasty, 'skipping')
            # else:
            print(id, p.natalFullname, 'entering now')
            while 'F' in [kin['kin'] for kin in p.kins] and str(p.id) not in data:
                for kin in p.kins:
                    if kin['kin'] == 'F':
                        p = CBDB.profile(kin['id'])
            id = p.id
            draw_tree(str(id))
            guid = recursion(str(id))
            # if guid is not None:
            #     webbrowser.open('https://www.geni.com/family-tree/index/' + str(guid))


def update(start=1):
    count = 0
    with open('CBDB2Geni.json', 'r+') as f:
        data = json.load(f)
        for id in data:
            count = count + 1
            if count > start:
                if count % 100 == 0:
                    print(count)
                guid = data[id]
                p = geni.profile(guid)
                if int(p.guid) != guid:
                    print("updating", id, guid, "->", p.guid)
                    data[id] = int(p.guid)
                    f.seek(0)
                    json.dump(data, f, indent=3)
        print('Number of ids updated:', count)


def open_Geni(id):
    id = str(id)
    with open('CBDB2Geni.json', 'r+') as f:
        data = json.load(f)
        if id in data:
            guid = data[id]
            p = geni.profile(guid)
            print(guid, p.guid)
            if p.guid != guid:
                f.seek(0)
                data[id] = p.guid
                json.dump(data, f, indent=3)
            webbrowser.open('https://www.geni.com/people/a/' + str(guid))
        else:
            print('not found')


def retrieve_all_ids():
    with open('CBDB2Geni.json', 'r') as f:
        all_ids = json.load(f)
    return all_ids


def fix_gender(id):
    all_ids = retrieve_all_ids()
    if str(id) in all_ids:
        guid = all_ids[str(id)]
        cp = CBDB.profile(id)
        if cp.id is None:
            print('id not found')
            return
        if cp.gender == 'female':
            gender = {'gender': 'female'}
            print(id, 'Female!', cp.natalFullname)
            p = geni.profile(guid)
            guid = p.guid
            geni.update(guid, gender)


def add_wife(i):
    cp = CBDB.profile(i)
    if cp.id is None:
        print(id, 'not found')
        return
    print(cp.natalFullname)
    print(cp.kins)


# for i in range(5000, 5428):
#     if i % 100 == 0:
#         print(i)
#     add_wife(i)


for i in range(10000, 20000):
    if i % 100 == 0:
        print(i)
    fix_gender(i)


# 53976 starting point of MQWW


def mass(start=56062, end=60000):
    all_ids = retrieve_all_ids
    for id in range(start, end):
        cp = CBDB.profile(id)
        if cp.id is not None:
            about_me = cp.notes
            sources = cp.rawdata.get('PersonSources', {}).get('Source', [])
            gender = cp.rawdata.get('BasicInfo', {}).get('Gender', '')
            if gender.isdigit():
                gender = int(gender)
            if type(sources) == dict:
                sources = [sources]
            for source in sources:
                if source.get('Source', '') == '明清婦女著作數據庫':
                    MQWW_id = source.get('Pages', '')
                    name = source.get('Notes', '')
                    if MQWW_id.isdigit() and '傳主為:' in name:
                        index = name.find(':')
                        name = name[index + 1:].split('.')[0]
                        MQWW_url = 'http://digital.library.mcgill.ca/mingqing/search/details-poet.php?poetID={}&showworks=1&showanth=1&showshihuaon=1&showpoems=&language=eng'.format(MQWW_id)
                        about_me = about_me + "\n\n--------\n\nMQWW: [{} {}]\n".format(MQWW_url, name)
                    if str(id) in all_ids:
                        guid = all_ids[str(id)]
                        print('updating', id, cp.natalFullname)
                    else:
                        guid = recursion(id)

                    gp = geni.profile(guid)
                    guid = gp.guid
                    data = cp.data
                    data['about_me'] = about_me
                    geni.update(guid, data)
                    geni.add_to_project(gp.guid, 47050)
                    break

            # if str(id) in all_ids:
            #     cp = CBDB.profile(id)
            #     guid = all_ids[str(id)]
            #     gp = geni.profile(guid)
            #     if gp.about_me != cp.notes:
            #         gp.update_about(cp.notes)
            #         print(id, 'updated:', cp.notes)
            # else:
            #     add_tree(id)

    # with open('CBDB2Geni.json', 'r') as f:
    #     data = json.load(f)
    # count = 0
    # for id in data:
    #     count = count + 1
    #     if count % 100 == 0:
    #         print(count)
    #     if count > start:
    #         guid = data[id]
    #         p = CBDB.profile(id)
    #         if 'Tackett' in p.notes or 'NewEpitaphID' in p.notes:
    #             pprint(p.natalFullname)
    #             geni.add_to_project(guid, 47011)
    #     if count > end:
    #         break


# mass(61000, 65000)
# print('done')

id = 13916  # 1384  #1385
# info(id)
# # pprint(CBDB.profile(id).rawdata)
# open_Geni(id)
# recursion(id)
# draw_tree(id)
# recursion(id)

# 呂蒙奇 ?-? 穎州下蔡 13093
