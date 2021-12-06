import asyncio
import logging
import ssl
import websockets
import traceback
import requests
import json
import time
import datetime
import string
from websockets.client import WebSocketClientProtocol



# r : 5 = moder
# r : 1 = user
# r : 6 = Admin


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('websockets')
logger.setLevel(logging.DEBUG)
TOKEN = 'secured'
ADMINS = [5,6]
PROMO_URL = 'https://api.csgorun.gg/discount'
MEDKIT_URL = 'https://api.csgorun.gg/use-medkit'
EXCHANGE_URL = 'https://api.csgorun.gg/marketplace/exchange-items'
prev_crashes =  []
inventory = []
cur_balance = '0.00'

message_2 = """
{"method":1,"params":{"channel":"u-noty#17787"},"id":2}
{"method":1,"params":{"channel":"online"},"id":3}
{"method":1,"params":{"channel":"game"},"id":4}
{"method":1,"params":{"channel":"bets"},"id":5}
{"method":1,"params":{"channel":"u-ub#17787"},"id":6}
{"method":1,"params":{"channel":"user-bet#17787"},"id":7}
{"method":1,"params":{"channel":"lottery"},"id":8}
{"method":1,"params":{"channel":"u-#17787"},"id":9}
{"method":1,"params":{"channel":"u-i#17787"},"id":10}
{"method":1,"params":{"channel":"noty#17787"},"id":11}
{"method":1,"params":{"channel":"sound#17787"},"id":12}
{"method":1,"params":{"channel":"withdraw-gift#17787"},"id":13}
{"method":1,"params":{"channel":"c-ru"},"id":14}
{"method":1,"params":{"channel":"medkit"},"id":15}
"""
def get_inv():
    response = requests.get(url='https://api.csgorun.gg/current-state?montaznayaPena=null',headers={'authorization': TOKEN})
    inv = []
    for item in response.json()['data']['user']['items']:
        inv.append(item['id'])
    return inv

def check_promo(msg):
    p = False
    if len(msg) >= 8 and len(msg) <= 12: 
        p = True
        for sym in msg:
            if not sym.isdigit() and sym not in string.ascii_lowercase:
                p = False
    if p == True:
        use_promo(msg)

def use_promo(promo):
    try:
        response = requests.post(url=PROMO_URL,json={'code':promo,'token':'null'},headers={'authorization':TOKEN})
        logging.info(f'{promo} promo sent!!!! \a')
        if response.ok:
            logging.info('+0.25')
        else:
            logging.info('promik gavno')
    except:
        traceback.print_exc()

def inv_header(msg):
    for added in msg['result']['data']['data']['newItems']:
        inventory.append(added['id'])
    for removed in msg['result']['data']['data']['removeItemIds']:
        inventory.remove(removed)
    logging.info(f'inventory is {inventory}')

def win_header(msg):
    cur_balance = msg['result']['data']['data']['balance']
    inventory.append(msg['result']['data']['data']['userItem']['id'])
    logging.info(f'inventory is {inventory}')
    logging.info(f'balance is {cur_balance}')    

def balance_header(msg):
    cur_balance = msg['result']['data']['data']['balance']
    logging.info(f'balance is {cur_balance}')

async def make_bet(cost):
    wish_id = [choose_wish(cost)]
    await asyncio.sleep(1)
    inv = [exchange(wish_id)]
    await asyncio.sleep(2)
    response = requests.post(url='https://api.csgorun.gg/make-bet',json={'userItemIds':inv,'auto':'1.20'},headers={'authorization':TOKEN})
    tries = 0
    while not response.ok and tries < 5:    
        inv = get_inv()
        logging.info(f'bet isnt made, code {response},trying again in 1,try:{tries}')
        await asyncio.sleep(1)
        response = requests.post(url='https://api.csgorun.gg/make-bet',json={'userItemIds':inv,'auto':'1.20'},headers={'authorization':TOKEN})
        tries += 1
    if response.ok:
        logging.info(f"bet made, success = {response.json()['success']}")
    else:
        logging.info(f'vse huinya(((( T_T')
        exit


def choose_wish(cost):
    response = requests.get(url = "https://cloud.this.team/csgo/items.json?v=1638190309928")
    if response.ok:
        costs = [cost-0.01*i for i in range(30)]
        items = {}
        for el in response.json()['data']:
            if el[6] in costs:
                items[el[6]] = el[0]
        for cst in costs:
            if items.get(cst):
                logging.info(f'wish id,cost: {items[cst],cst}')
                return items[cst]
        logging.info(f'wish code: {response}, no vse huinya')
    else:
        logging.info(f'wish code: {response}')

def exchange(wish_id):
    global inventory
    for i in range(5):
        try:
            response = requests.post(url=EXCHANGE_URL,json={'userItemIds':inventory,'wishItemIds':wish_id},headers={'authorization':TOKEN}) 
            if response.ok:
                logging.info('changed')
                return response.json()['data']['userItems']['newItems'][0]['id']
            else:
                logging.info(f'change is not success {response,inventory}, trying again in 2')
                inventory = get_inv()
                time.sleep(2)
        except:
            traceback.print_exc()

def use_medkit():
    try:
        time.sleep(2)
        response = requests.post(url=MEDKIT_URL,headers={'authorization':TOKEN})
        if response.ok:
            logging.info('medkit used')
        else:
            logging.info('medkit didnt used')
    except:
        traceback.print_exc()



async def consumer_handler(websocket: WebSocketClientProtocol) -> None:
    async for message in websocket:
        for line in message.split('\n'):
            if len(line) > 10:
                logging.info(len(asyncio.all_tasks()))
                asyncio.create_task(check_message(line))

async def consume(message1: dict,message2: list,hostname: str,port: int) -> None:
    websocket_resource_url = f"wss://{hostname}:{port}/connection/websocket"
    while True:
        async with websockets.connect(websocket_resource_url,ssl=ssl._create_unverified_context()) as websocket:
            try:
                await websocket.send(message1)
                await websocket.recv()
                await websocket.send(message2)
                await websocket.recv()
                await consumer_handler(websocket) 
            except websockets.ConnectionClosed:
                traceback.print_exc()
                continue

async def check_message(msg: str) -> None:
    msg = json.loads(msg)
    try:
        channel = msg['result']['channel']
        if channel == "c-ru":
            if msg['result']['data']['data']['p']['u']['r'] in ADMINS:
                check_promo(msg['result']['data']['data']['p']['c'])
        elif channel == "game":
            if msg['result']['data']['data']['type'] == 'c':
                await check_crush(msg)
        elif channel == "u-#17787":
            balance_header(msg)
        elif channel == "u-i#17787":
            inv_header(msg)
        elif channel == "u-ub#17787":
            win_header(msg)
        elif channel == 'medkit':
            use_medkit()
    except:
        logging.info(f'pizdec: {msg}',datetime.datetime.now())
        traceback.print_exc()

async def check_crush(msg):
    global prev_crashes
    global cur_balance
    crush = msg['result']['data']['data']['c']
    for i in range(len(prev_crashes)-1,0,-1):
        prev_crashes[i] = prev_crashes[i-1]
    prev_crashes[0] = crush
    if max(prev_crashes[:-1]) < 1.20 and cur_balance >= 0.25:
        await make_bet(cur_balance)
    elif max(prev_crashes[:2]) < 1.20 and cur_balance >= 0.25:
        await make_bet(4)

def get_started():
    global prev_crashes
    global cur_balance
    global inventory
    try:
        response = requests.get(url='https://api.csgorun.gg/current-state?montaznayaPena=null',headers={'authorization': TOKEN})
        if response.ok:
            cur_balance = response.json()['data']['user']['balance']
            crashes = response.json()['data']['game']['history']
            crashes.sort(key = lambda x: list(x.values())[0],reverse = True)
            for i in range(4,-1,-1):
                prev_crashes.append(crashes[i]['crash']) 
            inv = response.json()['data']['user']['items']
            for item in inv:
                inventory.append(item['id'])
            return response.json()['data']['centrifugeToken']
    except:
        
        traceback.print_exc()

if __name__ == '__main__':
    logger.addHandler(logging.StreamHandler())
    while True:
        try:
            message_1 = json.dumps({"params":{"token":get_started()},"id":1})
            asyncio.run(consume(message1=message_1,message2=message_2,hostname='ws.csgorun.gg',port=443))
            logging.info('vsyo govno')
        except:
            traceback.print_exc()
