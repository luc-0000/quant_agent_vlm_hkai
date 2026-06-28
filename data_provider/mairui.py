import json
import os
from time import sleep
import requests
from dateutil.parser import parser
import dotenv
dotenv.load_dotenv()

md_licence = os.getenv('MAIRUI_TOKEN')

class Mairui:
    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Mairui, cls).__new__(cls)
        return cls._instance

    def __init__(self, **kwargs,):
        if "period" in kwargs.keys():
            self.period = kwargs["period"]
        else:
            self.period = "daily"


    def get_my_data(self, base_url, stock_code, time_slot, repeat_time=10, cq='n', start_time=None, end_time=None):
        if time_slot is not None:
            url_sucession = stock_code + '/' + time_slot + '/' + cq + '/' + md_licence
        else:
            url_sucession = stock_code + '/' + md_licence


        if start_time is not None:
            url_sucession = url_sucession + '?st=' + start_time
        if end_time is not None:
            url_sucession = url_sucession + '&et=' + end_time

        stock_url = base_url + url_sucession
        headers = {'content-type': 'application/json'}
        # get stock basic
        for i in range(repeat_time):
            sleep(0.5)
            results = None
            r = requests.get(stock_url, headers=headers)
            r.encoding = "utf-8"
            if r.status_code != 200:
                print(r)
                # raise APIException('8801', 'Get data frm mydata server failed with status code: {}.'.format(r.status_code))
            elif r.text == '102' or r.text == '101':
                raise Exception('8802',
                                   'Licence not valid or reached the Limit with status code: {}.'.format(r.status_code))
            else:
                results = json.loads(r.text)
            if results is not None:
                break
        if results == [] or results == {} or results is None:
            print(r)
            raise Exception('8803', 'Stock data is empty with status code: {}.'.format(r.status_code))
        return results


    def get_today_open(self, stock_code, se):
        time_unit = self.get_time_unit()
        if 's' in stock_code:
            stock_url = 'https://api.mairuiapi.com/hsindex/latest/'
            stock_code = stock_code[2:]
            time_unit = 'd'
        else:
            stock_url = 'https://api.mairuiapi.com/hsstock/latest/'
        stock_full = stock_code + '.' + se.upper()
        r = self.get_my_data(stock_url, stock_full, time_unit)
        lastest_date = r[0].get('t')
        lastest_date = parser().parse(lastest_date)
        open_price = float(r[0].get('o'))
        return lastest_date, open_price


    def get_stock_cap(self, stock_code, se):
        if 's' in stock_code:
            # stock_url = 'http://api.mairuiapi.com/hsrl/ssjy/'
            # stock_code = stock_code[2:]
            # time_unit = 'd'
            return 0, 0
        else:
            stock_url = 'http://api.mairuiapi.com/hsrl/ssjy/'
        r =self.get_my_data(stock_url, stock_code, None)
        cap = round(float(r.get('sz')) / 100000000, 2)
        pe = float(r.get('pe'))
        return cap, pe


    def get_stock_history(self, symbol, start_time, end_time, time_slot):
        base_url = "http://api.mairuiapi.com/hsstock/history/"
        results = self.get_my_data(base_url, symbol, time_slot, start_time=start_time, end_time=end_time)
        return results
