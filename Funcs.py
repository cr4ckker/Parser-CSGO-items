import time, re, json, requests, os, queue, traceback
from random import randint, choice
from threading import Thread, currentThread
from urllib3.exceptions import ReadTimeoutError
from requests.exceptions import ConnectTimeout, ConnectionError, ReadTimeout, ProxyError

from sqlalchemy import Column, ForeignKey, Integer, String, Boolean, Float, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine

from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException
from selenium import webdriver

from Data import *

def Theme_session(session):
    if 'Theme' in session:
        if session['Theme'] == 'light':
            session['isLightTheme'] = True
        else:
            session['isLightTheme'] = False
        session.modified = True
    else:
        session['Theme'] = 'light'
        session['isLightTheme'] = True
        session.modified = True
        session.permanent = True
    return session['Theme']

# Нужно для запуска вне сервера
def DBSet():
    Base = declarative_base()

    class Item_Data(Base):  
        __tablename__ = 'items'
        id =                Column( Integer     , primary_key=True)  
        cost =              Column( Integer     , nullable=False)  
        value =             Column( Integer     , nullable=False)  
        name =              Column( String(60) , nullable=False, unique=True)   
        vanilla =           Column( Boolean     , nullable=False)  
        st =                Column( Boolean     , nullable=False)  
        souvenir =          Column( Boolean     , nullable=False)  
        item_name =         Column( String(60) , nullable=False)  
        skin =              Column( String(60) , nullable=False)  
        float_type =        Column( String(60) , nullable=False)  
        last_check=         Column( Integer )
        csgotm_volume=      Column( Integer ) 
        csgotm_value =      Column( Float   ) 
        csgotm_lastbuy =    Column( Integer ) 
        csgotm_in_mp=       Column( Float   ) 
        csgotm_out_mp=      Column( Float   ) 
        steamtm_volume =    Column( Integer ) 
        steamtm_value=      Column( Float   ) 
        steamtm_csgotm_mp=  Column( Float   ) 
        steamtm_in_mp=      Column( Float   )
        steamtm_out_mp=     Column( Float   )

    engine = create_engine('sqlite:///Items.db')
    Base.metadata.create_all(engine)
    Base.metadata.bind = engine
    DB = sessionmaker(bind=engine)
    Session = DB()
    return (Session, Item_Data)

class ParseService:
    def __init__(self, DB, log_lvl=1):
        self.chrome_options = Options()
        self.chrome_options.add_argument("--headless")
        self.chrome_options.add_argument('--no-sandbox')
        self.chrome_options.add_argument("--headless")
        self.chrome_options.add_argument("--disable-gpu")
        self.chrome_options.add_argument("--log-level=3")

        self.Session = DB
        self.log_lvl = log_lvl
        self.ITEMSLIST = dict()
        self.proxies = list()
        self.Proxy_BL = list()
        self.csgotm = queue.Queue()
        self.steamtm = queue.Queue()
        self.UpdateSteam = queue.Queue()
        self.UpdateCsgoTM = queue.Queue()
        self.logs = queue.Queue()

    def Start(self):
        ProxyParser = Thread(target=self.ProxyParse)
        CSGOTMParser = Thread(target=self.ParseCSGOTM)
        STEAMParser = Thread(target=self.ParseSTEAMTM)
        CSGO500Parser = Thread(target=self.ParseCSGO500)
        Updater = Thread(target=self.Update)
    
        ProxyParser.start()
        CSGO500Parser.start()
        CSGOTMParser.start()
        Updater.start()
        while len(self.proxies) == 0:
            time.sleep(0.5)
        STEAMParser.start()

    def Stop(self):
        ProxyParser.Enabled = False

    def log(self, text, debug=0):
        with open('Log.txt', 'w') as f:
            while True:
                log = logs.get()
                text, debug = (log[0], log[1])
                if self.log_lvl == 1 and not debug:
                    f.write(text)
                elif self.log_lvl == 2:
                    f.write(text)

    def ProxyParse(self):
        print("Proxy parser started")
        t = currentThread()
        while getattr(t, 'Enabled', True):
            if len(self.proxies) < 250:
                ips = ''
                try:
                    with webdriver.Chrome(WebDriverPath, chrome_options=self.chrome_options) as driver:
                        date = time.strftime('%Y-%m-%d',time.localtime(time.time()-54000))
                        driver.get(f'https://checkerproxy.net/archive/{date}')
                        while ips == '':
                            ips = driver.find_element_by_id('find_result').get_attribute('value') 
                            time.sleep(0.5)
                        self.proxies = re.findall(r'\d+\.\d+\.\d+\.\d+\:80', ips)
                        for pr in self.Proxy_BL:
                            if pr in self.proxies:
                                self.proxies.remove(pr)
                        logs.put([f'[PROXY] [INFO] Got new proxies! ({len(self.proxies)} got)', 0])
                except Exception as e:
                    logs.put([f'[PROXY] [ERROR] {e}', 0])
                    logs.put([traceback.format_exc(), 1])
                    continue
            time.sleep(1)


    def CSGO500PARSE(self, driver):
        for item in driver.find_element_by_id('market-shop-list').find_elements_by_css_selector('.market-item.market-listing-item'):
            name = item.find_element_by_css_selector('.market-item-name.listing-name').text
            if name == '':
                continue
            Item = ''
            Skin = ''
            Float = ''
            StatTrak = False
            Souvenir = False

            try:
                adjust = item.find_element_by_class_name('discount-gray').get_attribute('textContent')
            except:
                adjust = 0
            finally:
                adjust = 1 + int(''.join(re.findall(r'\d+', str(adjust))))/100

            value = ''.join(''.join(item.find_element_by_class_name('value').text.split('&nbsp;')).split(','))
            Item = name.split(' | ')[0]
            Item = Item.split('\u2605 ')[1] if re.match(r'^\u2605+ .+', Item) else Item
            if re.match(r'.*StatTrak\u2122+ .+', Item):
                Item = Item.split('StatTrak\u2122 ')[1] 
                StatTrak = True
            if re.match(r'.*Souvenir+ .+', Item):
                Item = Item.split('Souvenir ')[1] 
                Souvenir = True
            if re.match(r'(^(S|s)ticker .*)|(^(M|m)usic kit .*)', name):
                Skin = ' '.join(name.split(' | ')[1::])
            elif re.match(r'.+\(.+\)$', name):
                Skin = name.split(' | ')[1].split(' (')[0]
                Float = ''.join(re.findall(r'[A-Z]+', re.findall(r'\(.+\)', name)[0]))
            else:
                try:
                    Skin = ' '.join(name.split(' | ')[1::])
                    
                except:
                    Skin = 'Vanilla'
                    if f'{Item}' not in self.ITEMSLIST:
                        self.ITEMSLIST[f'{Item}'] = {
                                                'cost':int(''.join(value.split('(')[0].split(' '))), 
                                                'value':int(int(''.join(value.split('(')[0].split(' '))) // adjust), 
                                                'name':name,
                                                'vanilla':True,
                                                'st':StatTrak,
                                                'souvenir':Souvenir,
                                                'item_name':Item,
                                                'skin':Skin,
                                                'float_type':Float,
                                                'errors':[]
                                                }
                        self.csgotm.put(f'{Item} | {Skin} {Float}')
                        logs.put([f'[CSGO500] [INFO] {Item} | {Skin, Float} pushed to other parsing services', 0])
                        continue  
            if f'{Item} | {Skin} {Float}' not in self.ITEMSLIST:
                self.ITEMSLIST[f'{Item} | {Skin} {Float}'] = {
                                                        'cost':int(''.join(value.split('(')[0].split(' '))), 
                                                        'value':int(int(''.join(value.split('(')[0].split(' '))) // adjust), 
                                                        'name':name,
                                                        'vanilla':False,
                                                        'st':StatTrak,
                                                        'souvenir':Souvenir,
                                                        'item_name':Item,
                                                        'skin':Skin,
                                                        'float_type':Float,
                                                        'errors':[]
                                                        }
                self.csgotm.put(f'{Item} | {Skin} {Float}')
                logs.put([f'[CSGO500] [INFO] {Item} | {Skin, Float} pushed to other parsing services', 0])

    def ParseCSGO500(self):
        while True:
            try:
                with webdriver.Chrome(WebDriverPath, chrome_options=self.chrome_options) as driver:
                    logs.put(['Parsing Service Started', 0])
                    driver.get(CSGO500DATA['URL'])
                    for ck in CSGO500DATA['cookie']:
                        driver.add_cookie(ck)
                    driver.set_window_size(1920, 1080)
                    while True:
                        try:
                            driver.get(CSGO500DATA['URL'])
                            btn = WebDriverWait(driver, 10, 1).until(EC.visibility_of_element_located((By.CSS_SELECTOR, '.withdraw-option.withdraw-option-item')))
                            break
                        except TimeoutException:
                            logs.put(['[CSGO500] [ERROR] Эх, капча', 0])
                            time.sleep(15)
                            driver.get_screenshot_as_file('screen12.png')
                            try:
                                btn = WebDriverWait(driver, 10, 1).until(EC.visibility_of_element_located((By.CSS_SELECTOR, '.withdraw-option.withdraw-option-item')))
                                break
                            except:
                                pass
                    
                    driver.get_screenshot_as_file('screen1.png')
                    webdriver.ActionChains(driver).click(btn).perform()
                    # time.sleep(1)
                    # # btn = driver.find_element_by_css_selector('.btn-toolbar.dropdown-button.shop-filter')
                    # # webdriver.ActionChains(driver).click(btn).perform()
                    # # time.sleep(2)
                    # # btn = driver.find_element_by_id('p2p-sort-filter').find_elements_by_class_name('shop-filter-option')[1]
                    # # webdriver.ActionChains(driver).click(btn).perform()
                    time.sleep(2)
                    driver.get_screenshot_as_file('CSGOMARKET.png')
                    self.CSGO500PARSE(driver)

                    while True:
                        if not self.csgotm.qsize() and not self.steamtm.qsize():
                            btn = driver.find_element_by_css_selector('.btn.btn-toolbar.btn-pagination-next')
                            webdriver.ActionChains(driver).click(btn).perform()
                            time.sleep(2)
                            if driver.find_element_by_id('market-shop-empty').get_attribute('style') == 'display: none;':
                                self.CSGO500PARSE(driver)
                            else:
                                break
                        time.sleep(10)
                    logs.put(['[CSGO500] [INFO] Parsing Service ended work', 0])
            except Exception as e:
                logs.put([f'[CSGO500] [ERROR]: {e}', 0])
                logs.put([traceback.format_exc(), 1])

    def ParseCSGOTM(self):
        print('CSGOTM parser started')
        while True:
            try:
                with webdriver.Chrome(WebDriverPath, chrome_options=self.chrome_options) as driver:
                    item = self.csgotm.get()
                    logs.put([f"[CSGOTM] [INFO] Got item({item}), parsing", 0])
                    now_time = int(time.time())
                    n=0
                    value = 0
                    reserveItems = {'number':0}
                    driver.set_page_load_timeout(12)
                    driver.get(CSGOTMDATA['URL']+f"?s=price&q={Float_definitions[self.ITEMSLIST[item]['float_type']][0] if self.ITEMSLIST[item]['float_type'] in Float_definitions else ''}&h={'StatTrak™,★,★ StatTrak™' if self.ITEMSLIST[item]['st'] else ''}&search={'Souvenir ' if self.ITEMSLIST[item]['souvenir'] else ''}{self.ITEMSLIST[item]['item_name']} {self.ITEMSLIST[item]['skin']}&fst=0&sd=asc")
                    time.sleep(0.4)
                    driver.get_screenshot_as_file(f"csgotm_screens/csgotm_{self.ITEMSLIST[item]['item_name']}_{self.ITEMSLIST[item]['skin']}.png")
                    Items_len = len(driver.find_element_by_class_name('market-items').find_elements_by_class_name('item')) 
                    if Items_len > 1:
                        for i in range(1, Items_len):
                            time.sleep(0.3)
                            try:
                                ITEM_ID = '_'.join(driver.find_element_by_class_name('market-items').find_elements_by_class_name('item')[i].get_attribute('href').split('/item/')[1].split('-')[:2:])
                                Item_Info = json.loads(requests.post(f"{CSGOTMDATA['API']}{ITEM_ID}/?key={CSGOTMDATA['token']}").text)
                                if 'error' not in Item_Info:
                                    if Item_Info['number'] > reserveItems['number']:
                                        reserveItems = Item_Info.copy()
                                        if Item_Info['number'] < 200:
                                            continue
                                        break
                            except:
                                continue
                        if reserveItems['number'] > 0:
                            Item_Info = reserveItems.copy()
                        else:
                            continue
                        if 'error' in Item_Info:
                            logs.put([Item_Info['error'], 0])
                            continue
                        if Item_Info['success']:
                            
                            if now_time - int(Item_Info['history'][-1]['l_time']) > 86400 and now_time - int(Item_Info['history'][0]['l_time']) < 86400:
                                for n in range(Item_Info['number']):
                                    if now_time - int(Item_Info['history'][n]['l_time']) > 86400:
                                        Item_history = Item_Info['history'][:n:]
                                        break
                                volume = 'Очень часто' if n > 35 else 'Часто' if n > 20 else 'Умеренно' if n > 8 else 'Редко' if n > 3 else 'Очень редко' if n > 1 else "Крайне редко"
                            else:
                                n=60 if Item_Info['number'] > 60 else 10 if now_time - int(Item_Info['history'][0]['l_time']) < 86400 and Item_Info['number'] > 10 else Item_Info['number']
                                Item_history = Item_Info['history'][:n:]
                                volume = 'Очень часто' if now_time - int(Item_Info['history'][0]['l_time']) < 86400 else "Крайне редко"

                            for act in Item_history:
                                value += int(act['l_price'])/100
                            value /= n
                        else:
                            volume = None
                            value = None
                        self.ITEMSLIST[item]['csgotm_volume'] = volume
                        self.ITEMSLIST[item]['csgotm_value'] = round(value, 2)
                        self.ITEMSLIST[item]['csgotm_lastbuy'] = int(Item_Info['history'][0]['l_time'])
                        self.ITEMSLIST[item]['csgotm_in_mp'] = round(self.ITEMSLIST[item]['value']/value, 2)
                        self.ITEMSLIST[item]['csgotm_out_mp'] = round(self.ITEMSLIST[item]['cost']/value, 2)
                        
                    else:
                        self.ITEMSLIST[item]['csgotm_volume'] = None
                        self.ITEMSLIST[item]['csgotm_value'] = None
                        self.ITEMSLIST[item]['csgotm_lastbuy'] = None
                        self.ITEMSLIST[item]['csgotm_in_mp'] = None
                        self.ITEMSLIST[item]['csgotm_out_mp'] = None
                        self.ITEMSLIST[item]['errors'].append('Not parsed CSGOTM')
                    self.ITEMSLIST[item]['last_check'] = time.ctime(now_time)
                    self.steamtm.put(item)
                    self.UpdateCsgoTM.put(item)
                    logs.put([f'[CSGOTM] [INFO] Got info for {item} on CSGOTM. Items left: {self.csgotm.qsize()}', 0])
            except Exception as e:
                logs.put([f'[CSGOTM] [ERROR] ({item}): {e}', 0])
                logs.put([traceback.format_exc(), 1])
                self.csgotm.put(item)
                continue

    def ParseSTEAMTM(self):
        proxy = None
        good_proxies = list()
        print('SteamTM parser started')
        while True:
            Item = self.steamtm.get()
            logs.put([f"[STEAM] [INFO] Got item({Item}), parsing", 0])
            try:
                if len(self.proxies) == 0 and len(good_proxies) > 0:
                    self.proxies = good_proxies
                if proxy is None:
                    proxy = choice(self.proxies)
                    timeout = 8
                    success_reqs = 0
                else:
                    time.sleep(2)
                    timeout = 10

                resp = requests.post(f'https://steamcommunity.com/market/priceoverview/?currency=5&country=ru&appid=730&market_hash_name={self.ITEMSLIST[Item]["name"]}&format=json', proxies={'https':f'https://{proxy}'}, timeout=timeout)
                if resp.status_code == 403:
                    if proxy in self.proxies:
                        self.proxies.remove(proxy)
                    proxy = None
                    success_reqs = 0
                    logs.put([f'[STEAM] [ERROR] Forbidden proxy (Left: {len(self.proxies)})', 0])
                    self.steamtm.put(Item)
                    self.Proxy_BL.append(proxy)
                    if proxy in good_proxies:
                        good_proxies.remove(proxy)
                    continue
                if resp.text:
                    Item_info = json.loads(resp.text)
                    if Item_info is not None:
                        if Item_info['success']:  
                            success_reqs +=1
                            if 'volume' in Item_info:     
                                volume = int(''.join(Item_info['volume'].split(',')))
                                value = float(Item_info["median_price"].split(' pуб.')[0].replace(',', '.'))
                            elif Item_info.get('lowest_price'):
                                volume = 0
                                value = float(Item_info["lowest_price"].split(' pуб.')[0].replace(',', '.'))
                            else:
                                self.ITEMSLIST[Item]['steamtm_volume'] = None
                                self.ITEMSLIST[Item]['steamtm_value'] = None
                                self.ITEMSLIST[Item]['steamtm_csgotm_mp'] = None
                                self.ITEMSLIST[Item]['steamtm_in_mp'] = None
                                self.ITEMSLIST[Item]['steamtm_out_mp'] = None
                                self.ITEMSLIST[Item]['errors'].append('Not parsed Steam')
                                self.UpdateSteam.put(Item)
                                logs.put([f'[STEAM] [INFO] Got empty info for {Item} on Steam. Items left: {self.steamtm.qsize()}', 0])
                                continue
                            self.ITEMSLIST[Item]['steamtm_volume'] = volume
                            self.ITEMSLIST[Item]['steamtm_value'] = value
                            if 'Not parsed CSGOTM' not in self.ITEMSLIST[Item]['errors']:
                                self.ITEMSLIST[Item]['steamtm_csgotm_mp'] = round(self.ITEMSLIST[Item]['csgotm_value']/value, 2)
                            else:
                                self.ITEMSLIST[Item]['steamtm_csgotm_mp'] = None
                            self.ITEMSLIST[Item]['steamtm_in_mp'] = round(self.ITEMSLIST[Item]['value']/value, 2)
                            self.ITEMSLIST[Item]['steamtm_out_mp'] = round(self.ITEMSLIST[Item]['cost']/value, 2)
                            self.UpdateSteam.put(Item)
                            logs.put([f'[STEAM] [INFO] Got info for {Item} on Steam. Items left: {self.steamtm.qsize()}', 0])
                        else:
                            self.ITEMSLIST[Item]['steamtm_volume'] = None
                            self.ITEMSLIST[Item]['steamtm_value'] = None
                            self.ITEMSLIST[Item]['steamtm_csgotm_mp'] = None
                            self.ITEMSLIST[Item]['steamtm_in_mp'] = None
                            self.ITEMSLIST[Item]['steamtm_out_mp'] = None
                            self.ITEMSLIST[Item]['errors'].append('Not parsed Steam')
                            self.UpdateSteam.put(Item)
                            logs.put([f'[STEAM] [INFO] Got info for {Item} on Steam. Items left: {self.steamtm.qsize()}', 0])
                    else:
                        logs.put([f'[STEAM] [ERROR] Rate limit reached {resp.status_code}', 0])
                        self.steamtm.put(Item)
                        if proxy in self.proxies:
                            self.proxies.remove(proxy)
                        if success_reqs < 2:
                            proxy = None
                        else:
                            if proxy not in good_proxies:
                                good_proxies.append(proxy)
                        success_reqs = 0
                else:
                    logs.put(['[STEAM] [ERROR] Empty Response', 0])
                    self.steamtm.put(Item)
                    time.sleep(0.5)
            except ConnectTimeout:
                logs.put([f'[STEAM] [ERROR] dead proxy (Left: {len(self.proxies)})', 0])
                self.steamtm.put(Item)
                if proxy in self.proxies:
                    self.proxies.remove(proxy)
                if success_reqs < 2:
                    proxy = None
                else:
                    if proxy not in good_proxies:
                        good_proxies.append(proxy)
                success_reqs = 0
            except ProxyError:
                logs.put([f'[STEAM] [ERROR] dead proxy (Left: {len(self.proxies)})', 0])
                self.steamtm.put(Item)
                if proxy in self.proxies:
                    self.proxies.remove(proxy)
                if success_reqs < 2:
                    proxy = None
                    self.Proxy_BL.append(proxy)
                else:
                    if proxy not in good_proxies:
                        good_proxies.append(proxy)
                success_reqs = 0
            except ConnectionError:
                logs.put([f'[STEAM] [ERROR] dead proxy (Left: {len(self.proxies)})', 0])
                self.steamtm.put(Item)
                if proxy in self.proxies:
                    self.proxies.remove(proxy)
                if success_reqs < 2:
                    proxy = None
                    self.Proxy_BL.append(proxy)
                else:
                    if proxy not in good_proxies:
                        good_proxies.append(proxy)
                success_reqs = 0
            except ReadTimeout:
                logs.put([f'[STEAM] [ERROR] dead proxy (Left: {len(self.proxies)})', 0])
                self.steamtm.put(Item)
                if proxy in self.proxies:
                    self.proxies.remove(proxy)
                if success_reqs < 2:
                    proxy = None
                    self.Proxy_BL.append(proxy)
                else:
                    if proxy not in good_proxies:
                        good_proxies.append(proxy)
                success_reqs = 0
            except ReadTimeoutError:
                logs.put([f'[STEAM] [ERROR] dead proxy (Left: {len(self.proxies)})', 0])
                self.steamtm.put(Item)
                if proxy in self.proxies:
                    self.proxies.remove(proxy)
                if success_reqs < 2:
                    proxy = None
                    self.Proxy_BL.append(proxy)
                else:
                    if proxy not in good_proxies:
                        good_proxies.append(proxy)
                success_reqs = 0
            except Exception as e:
                logs.put(['[STEAM] [ERROR]:', e, 0])
                logs.put([traceback.format_exc(), 1])
                logs.put([resp.status_code, 1])
                self.steamtm.put(Item)
                continue
    def Update(self):
        Items2Update = dict()
        print('Update Service started')
        while True:
            Item = None
            try:
                Item = self.UpdateCsgoTM.get_nowait()
                if Item in Items2Update:
                    Items2Update[Item]['CSGOTM'] = True
                else:
                    Items2Update[Item] = dict(CSGOTM = True, Steam = False)
            except:
                pass
            try:
                Item = self.UpdateSteam.get_nowait()
                if Item in Items2Update:
                    Items2Update[Item]['Steam'] = True
                else:
                    Items2Update[Item] = dict(CSGOTM = False, Steam = True)
            except:
                pass
            if Item is not None:
                if Items2Update[Item]['Steam'] and Items2Update[Item]['CSGOTM']:
                    self.ITEMSLIST[Item].pop('errors')
                    if self.Session.query(Item_Data).filter_by(name=self.ITEMSLIST[Item]['name']).first() is None:
                        self.Session.add(Item_Data(**self.ITEMSLIST[Item]))
                    else:
                        ITEM = self.Session.query(Item_Data).filter_by(name=self.ITEMSLIST[Item]['name']).first()
                        ITEM.cost = self.ITEMSLIST[Item]['cost']
                        ITEM.value = self.ITEMSLIST[Item]['value']
                        ITEM.last_check = self.ITEMSLIST[Item]['last_check']
                        if self.ITEMSLIST[Item]['csgotm_volume']:
                            ITEM.csgotm_volume = self.ITEMSLIST[Item]['csgotm_volume'] 
                        if self.ITEMSLIST[Item]['csgotm_value']:
                            ITEM.csgotm_value = self.ITEMSLIST[Item]['csgotm_value']
                        if self.ITEMSLIST[Item]['csgotm_lastbuy']:
                            ITEM.csgotm_lastbuy = self.ITEMSLIST[Item]['csgotm_lastbuy'] 
                        if self.ITEMSLIST[Item]['csgotm_in_mp']:
                            ITEM.csgotm_in_mp = self.ITEMSLIST[Item]['csgotm_in_mp'] 
                        if self.ITEMSLIST[Item]['csgotm_out_mp']:
                            ITEM.csgotm_out_mp = self.ITEMSLIST[Item]['csgotm_out_mp'] 
                        if self.ITEMSLIST[Item]['steamtm_volume']:
                            ITEM.steamtm_volume = self.ITEMSLIST[Item]['steamtm_volume'] 
                        if self.ITEMSLIST[Item]['steamtm_value']:
                            ITEM.steamtm_value = self.ITEMSLIST[Item]['steamtm_value'] 
                        if self.ITEMSLIST[Item]['steamtm_csgotm_mp']:
                            ITEM.steamtm_csgotm_mp = self.ITEMSLIST[Item]['steamtm_csgotm_mp'] 
                        if self.ITEMSLIST[Item]['steamtm_in_mp']:
                            ITEM.steamtm_in_mp = self.ITEMSLIST[Item]['steamtm_in_mp'] 
                        if self.ITEMSLIST[Item]['steamtm_out_mp']:
                            ITEM.steamtm_out_mp = self.ITEMSLIST[Item]['steamtm_out_mp'] 

                        self.Session.add(ITEM)
                    self.Session.commit()
                    self.ITEMSLIST.pop(Item)
                    Items2Update.pop(Item)
                    logs.put(['[UPDATER] [INFO] Информация о ', Item, "Успешно сохранена!", 0])

if __name__ == '__main__':
    DBSession, Item_Data = DBSet()
    p = ParseService(DBSession)
    p.Start()