import json
import random
import time
import requests


from threading import Thread
from pymongo import MongoClient
from header import get_request_header


class Mhxy(object):

    def __init__(self, start, end):
        self.start = start
        self.end = end
        self.time = str(int(time.time()*1000))
        # _=代表时间戳, level分别代表了两个等级区间, server_type为定值不变, page页码, 其余定值不变, 如果需要指定门派可以增加school参数
        # self.url = 'https://recommd.xyq.cbg.163.com/cgi-bin/recommend.py?_={}&level_min=175&level_max=175&school=5&act=recommd_by_role&page={}'.format(self.time, self.page)
        self.headers = get_request_header()
        self.bproxy = requests.get('http://118.25.93.211:16688/random?protocol=http&nick_type=2', headers=self.headers)
        self.proxy = {
            'http': self.bproxy.content.decode()
        }
        self.client = MongoClient('127.0.0.1', 27017)
        # 选择一个数据库
        self.db = self.client['admin']
        # 这里是认证登录所以需要进入admin进行登录, 不使用auth认证登录的mongo可以忽略
        self.db.authenticate('账号', '密码')
        # 选择一个集合
        self.col = self.client['test']['175_mhxy']
        self.info = 'return_url=; _ntes_nnid=510cab6547aa0e440af816dde796c00d,1576391392098; _ntes_nuid=510cab6547aa0e440af816dde796c00d; fingerprint=u8xbeja3vzkavszi; __session__=1; area_id=1; cbg_qrcode=dX-NS21tu_SXXA547UqK9iw1sQbqOyIq6AhO86u2; sid=yVKAKllBcWusoGzN3RaSMdi9XVKJHMDjkYVbIHT5; cur_servername=%25E7%258F%258D%25E5%25AE%259D%25E9%2598%2581; wallet_data=%7B%22is_locked%22%3A%20false%2C%20%22checking_balance%22%3A%200%2C%20%22balance%22%3A%200%2C%20%22free_balance%22%3A%200%7D; last_login_roleid=32312910; login_user_nickname=%25E5%2588%25AB%25E6%2589%2593%25E6%2584%259F%25E6%2583%2585%25E7%2589%258C; is_user_login=1; login_user_icon=203; login_user_roleid=32312910; login_user_level=30; login_user_urs=m18861816385@163.com; login_user_school=3; new_msg_num=13; offsale_num=0; unpaid_order_num=0; unpaid_order_price_total=0.00; last_login_role_serverid=358; recommend_typeids=1,2,3,4; recommend_url=https://xyq.cbg.163.com/cgi-bin/query.py?act=recommend_search&recommend_type=1; last_login_serverid=358; remind_offsale=1; alert_msg_flag=1'
        self.cookie = {cookie.split('=')[0]: cookie.split('=')[-1]for cookie in self.info.split(';')}

    def request_url(self):
        for page in range(self.start, self.end + 1):
            url = 'https://recommd.xyq.cbg.163.com/cgi-bin/recommend.py?_={}&level_min=175&level_max=175&school=5&act=recommd_by_role&page={}'.format(self.time, page)
            response = requests.get(url, headers=self.headers, proxies=self.proxy)
            time.sleep(random.uniform(1, 3))
            data_dict = json.loads(response.content.decode())
            role = []
            for data in data_dict['equips']:
                role_dict = {}
                highlight = []
                role_dict['role_name'] = data['seller_nickname']
                role_dict['role_id'] = data['seller_roleid']
                role_dict['role_price'] = data['price']
                role_dict['role_level'] = data['equip_level_desc']
                role_dict['server_name'] = data['server_name']
                role_dict['role_selling_time'] = data['selling_time']
                role_dict['role_time_left'] = data['time_left']
                role_dict['role_link'] = 'https://xyq.cbg.163.com/equip?s={0}&eid={1}'.format(data['server_id'], data['eid'])
                highlights = data['highlights']if data['highlights'] else ''
                if highlights:
                    for i in highlights:
                        highlight.append(i[0])
                role_dict['highlights'] = highlight
                role.append(role_dict)
            print('----------------------{}-----------------------'.format(page))
            yield from role

    def save(self, role):
        for index, value in enumerate(role):
            count = self.col.count_documents({'_id': value['role_name']})
            if count == 0:
                dict = value
                dict['_id'] = value['role_name']
                self.col.insert(dict)
                print('插入第角色:{}'.format(value['role_name']))
            else:
                print('已存在角色:{}'.format(value['role_name']))

    @classmethod
    def run(cls, *args):
        a = cls(*args)
        role = a.request_url()
        a.save(role)

def main():
    # 开启4个进程，传入爬取的页码范围
    thead_list = []
    t1 = Thread(target=Mhxy.run, args=(1, 25))
    t1.start()
    t2 = Thread(target=Mhxy.run, args=(26, 50))
    t2.start()
    t3 = Thread(target=Mhxy.run, args=(51, 75))
    t3.start()
    t4 = Thread(target=Mhxy.run, args=(76, 100))
    t4.start()

    thead_list.append(t1)
    thead_list.append(t2)
    thead_list.append(t3)
    thead_list.append(t4)

    for t in thead_list:
        t.join()



if __name__ == '__main__':
    b = time.time()
    main()
    d = time.time()
    print('耗时:%s' % (d - b))
