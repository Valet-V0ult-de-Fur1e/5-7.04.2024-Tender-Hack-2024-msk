class WildberriesParser:
    """
    "www.wildberries.ru"
    detail.aspx - описание basket

    options - характеристики (это лист)
    selling.brand_name - бренд
    subj_name - подкатегория
    subj_root_name - категория
    imt_name - название
    """

    @classmethod
    def get_busket(cls, id_p):
        _short_id = id_p // 100000
        if 0 <= _short_id <= 143:
            basket = '01'
        elif 144 <= _short_id <= 287:
            basket = '02'
        elif 288 <= _short_id <= 431:
            basket = '03'
        elif 432 <= _short_id <= 719:
            basket = '04'
        elif 720 <= _short_id <= 1007:
            basket = '05'
        elif 1008 <= _short_id <= 1061:
            basket = '06'
        elif 1062 <= _short_id <= 1115:
            basket = '07'
        elif 1116 <= _short_id <= 1169:
            basket = '08'
        elif 1170 <= _short_id <= 1313:
            basket = '09'
        elif 1314 <= _short_id <= 1601:
            basket = '10'
        elif 1602 <= _short_id <= 1655:
            basket = '11'
        elif 1656 <= _short_id <= 1919:
            basket = '12'
        elif 1920 <= _short_id <= 2045:
            basket = '13'
        elif 2046 <= _short_id <= 2189:
            basket = '14'
        elif 2091 <= _short_id <= 2405:
            basket = '15'
        else:
            basket = '16'
        return basket

    @classmethod
    def wrapper_while_not_true(cls, func, *param):
        flag = False 
        res = None
        while flag == False:
            try:
                res = func(*param)
                flag = True
            except Exception as err:
                # print(err)
                pass
        return res

    @classmethod
    def explicitly_get_product_info(cls, name):
        import requests as req 


        ref = f'https://search.wb.ru/exactmatch/ru/common/v5/search?ab_testing=false&appType=1&curr=rub&dest=-1257786&query={name}&resultset=catalog&sort=popular&spp=30&suppressSpellcheck=false'
        # print(ref)
        res_cat_json = req.get(ref).json()
        id_p = res_cat_json['data']['products'][0]['id'] # first product
        # print(id_p)
        ref_card = f'https://basket-{cls.get_busket(id_p)}.wbbasket.ru/vol{str(id_p)[:-5]}/part{str(id_p)[:-3]}/{id_p}/info/ru/card.json'
        # print(ref_card)
        res_card_json = req.get(ref_card).json()
        prod_features = res_card_json
        return prod_features

    @classmethod
    def get_product_info(cls, name):
        res = cls.wrapper_while_not_true(cls.explicitly_get_product_info, name)
        res = {
            'brand': res['selling']['brand_name'],
            'category': res['subj_root_name'], 
            'features': res['options']
        }
        return res
    

class AptekaParser:
    """
    brand. ... - бренд
    humanableUrl - ссылка на товар
    product.iteminfo.5e326db1ca7bdc000192f710.attributesForSearch
    """
    @classmethod
    def get_product_info(cls, name):
        import requests as req 
        from bs4 import BeautifulSoup
        import json
        headers = {
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive',
            'Origin': 'https://apteka.ru',
            'Referer': 'https://apteka.ru/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Mobile Safari/537.36',
            'device-id': '1712439876709_5ac2d767c2bb6',
            'sec-ch-ua': '"Google Chrome";v="123", "Not:A-Brand";v="8", "Chromium";v="123"',
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-platform': '"Android"',
            'user-session-id': 'SDI_f782d2g28dc70a5255J_8q95203l74E66Y73A81Q/',
            'x-dreg-tst': '1712439876713',
            'x-session-id': '765fea1a-7d67-bba8-198a-0dddd430e1bd',
            'ym-aru-visorc': 'ZG50OjA7dzowO2M6MDtkcHI6MS4yNTtzY0RwdDoyNC8yNDtzY1dkOjE1MzY7c2NIdDo4NjQ7d25PV2Q6MTUzNjt3bk9IdDo4MjQ7d25JV2Q6MTUzNjt3bklIdDo3Mzg7Y2xpV2Q6MTUxOTtjbGlIdDo3Mzg7d25YOjA7d25ZOjA7d25Ic3RMbjozO3R6Oi02MDA7cHQ6V2luMzI7Y2g4NDp0cnVlO2NoMDA6dHJ1ZTtjaDEwOnRydWU7Y2gxNTp0cnVlO2NoMTk6dHJ1ZTtjaDIxOnRydWU7',
        }

        params = {
            'page': '0',
            'pageSize': '25',
            'iPharmTownId': '',
            'withprice': 'false',
            'withprofit': 'false',
            'withpromovits': 'false',
            'phrase': name,
        }

        res = req.get('https://api.apteka.ru/Search/ByPhrase', params=params, headers=headers)
        res = res.json()['result']
        if res:
            ref_prod = f'https://apteka.ru/product/{res[0]["humanableUrl"]}'
            res = req.get(ref_prod).text
            soup = BeautifulSoup(res, 'html.parser')
            soup = soup.find('head')
            soup = soup.find_all('script')[-1]
            data_json = json.loads(soup.text.lstrip('window.__INITIAL_STATE__ = '))
            data_json = json.loads(soup.text.lstrip('window.__INITIAL_STATE__ = '))
            # product.iteminfo.5e326db1ca7bdc000192f710.attributesForSearch
            data_json = data_json['product']['iteminfo']
            keys = list(data_json)
            data_json = data_json[keys[0]]
            data_json_features = data_json['attributesForSearch']
            features = []
            for i in data_json_features:
                value = ';'.join([str(j['name']) for j in i['valuesInfo']])
                features.append({'name': i['name'], 'value': value})
            res = {
                'brand': data_json['brandDescription']['name'],
                'category': data_json['category']['name'], 
                'features': features
            }
            return res
        return None
    

# print(AptekaParser.get_product_info('презервативы дюрекс'))
# print(WildberriesParser.get_product_info('Аммиак 10%'))
# print(WildberriesParser.get_product_info('Ноутбук Lenovo'))