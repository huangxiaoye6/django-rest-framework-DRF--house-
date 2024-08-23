import re

import pymysql
import requests


class LianJia(object):
    def __init__(self):
        self.url = 'https://cq.lianjia.com/ershoufang/{0}/pg{1}/'
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0.0'
        }

        self.db = pymysql.connect(host='localhost', user='root', password='123456', database='house', port=3306,
                                  charset='utf8')
        self.cursor = self.db.cursor()
        self.area = {
            'jiangbei': '江北区', 'yubei': '渝北区', 'nanan': '南岸区', 'banan': '巴南区', 'shapingba': '沙坪坝区',
            'jiulongpo': '九龙坡区', 'yuzhong': '渝中区', 'dadukou': '大渡口区', 'jiangjing': '江津区',
            'beibei': '北碚区',
            'kaizhouqu': '开州区', 'wushanxian1': '巫山县', 'wuxixian': '巫溪县',
            'xiushantujiazumiaozuzizhixian': '秀山土家族苗族自治县',
            'youyangtujiazumiaozuzizhixian': '酉阳土家族苗族自治县', 'rongchangqu': '荣昌区',
            'pengshuimiaozutujiazuzizhixian': '彭水苗族土家族自治县',
            'zhongxian': '忠县', 'fengjiexian': '奉节县', 'dianjiangxian': '垫江县', 'chengkouxian': '城口县',
            'tongliang': '铜梁区', 'bishan': '璧山区',
            'hechuang': '合川区', 'changshou1': '长寿区', 'wanzhou': '万州区', 'fuling': '涪陵区'
        }

    def get_content(self):
        content_dict = {}
        for key, value in self.area.items():
            for page in range(1, 100):
                response = requests.get(self.url.format(key, page), headers=self.headers)
                content = response.text
                content_dict['content'] = content
                content_dict['city'] = value
                print('正在爬取{0}的第{1}页!'.format(value, page))
                yield content_dict

    def sparse_content(self, content):
        result = re.compile(
            r' data-original="(?P<img>.*?)".*?data-is_focus="" data-sl="">(?P<title>.*?)</a>.*?data-el="region">(?P<region>.*?)</a>.*?'
            r' <a href=".*?" target="_blank">(?P<area>.*?)</a>.*?<span class="houseIcon"></span>(?P<houseInfo>.*?)</div>.*?'
            r'<span class="starIcon"></span>(?P<staus>.*?)</div>.*?<span class="">(?P<total_price>.*?)</span>.*?'
            r'data-price=".*?"><span>(?P<single_price>.*?)</span>', re.S)
        for item in content:
            data = result.finditer(item['content'])
            for i in data:
                data_dict = i.groupdict()
                houseInfo_length = len(data_dict['houseInfo'].split('|'))
                if houseInfo_length == 7 or houseInfo_length == 8:
                    data_dict['house_type'] = data_dict['houseInfo'].split('|')[0]
                    data_dict['house_size'] = data_dict['houseInfo'].split('|')[1]
                    data_dict['toward'] = data_dict['houseInfo'].split('|')[2]
                    data_dict['decoration'] = data_dict['houseInfo'].split('|')[3]
                    data_dict['floor'] = data_dict['houseInfo'].split('|')[4]
                    data_dict['year'] = data_dict['houseInfo'].split('|')[5]
                    data_dict['year'] = data_dict['year'].strip()
                    data_dict['building_type'] = data_dict['houseInfo'].split('|')[6]
                    data_dict['building_type'] = data_dict['building_type'].strip()
                else:
                    data_dict['house_type'] = data_dict['houseInfo'].split('|')[0]
                    data_dict['house_size'] = data_dict['houseInfo'].split('|')[1]
                    data_dict['toward'] = data_dict['houseInfo'].split('|')[2]
                    data_dict['decoration'] = data_dict['houseInfo'].split('|')[3]
                    data_dict['floor'] = data_dict['houseInfo'].split('|')[4]
                    data_dict['building_type'] = data_dict['houseInfo'].split('|')[5]
                    data_dict['building_type'] = data_dict['building_type'].strip()
                    data_dict['year'] = ''
                data_dict['view'] = data_dict['staus'].split('/')[0]
                data_dict['view'] = data_dict['view'].replace('人关注', '')
                data_dict['release_time'] = data_dict['staus'].split('/')[1]
                data_dict['single_price'] = data_dict['single_price'].strip('元/平')
                data_dict['single_price'] = data_dict['single_price'].replace(',', '')
                data_dict['region'] = data_dict['region'].strip()
                data_dict['city'] = item['city']
                yield data_dict

    def Save_MySQL(self, data_dict):
        for data in data_dict:
            sql = """  
                    INSERT INTO houseInfo (city,title, region, area, house_type, house_size, toward, decoration, floor, building_type, year, view_num, release_time, single_price, total_price,img)  
                    VALUES (%s,%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,%s)  
                    """
            self.cursor.execute(sql, (
                data['city'],
                data['title'],
                data['region'],
                data['area'],
                data['house_type'],
                data['house_size'],
                data['toward'],
                data['decoration'],
                data['floor'],
                data['building_type'],
                data['year'],
                data['view'],
                data['release_time'],
                data['single_price'],
                data['total_price'],
                data['img']
            ))
            self.db.commit()

    def main(self):
        columns = """CREATE TABLE IF NOT EXISTS houseInfo (
                        id INT AUTO_INCREMENT PRIMARY KEY,city char(8), title char(56), region char(32),  area char(8),  house_type char(8),
                        house_size char(16),  toward char(16),  decoration char(8),floor char(16),  building_type VARCHAR(8),
                        year char(8),  view_num int,  release_time char(16),  single_price int, total_price int,img char(128)) """
        self.cursor.execute(columns)
        content = self.get_content()
        data_dict = self.sparse_content(content)
        self.Save_MySQL(data_dict)
        self.cursor.close()
        self.db.close()


if __name__ == '__main__':
    lianJia = LianJia()
    lianJia.main()
