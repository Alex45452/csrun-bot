import asyncio
import logging
import random
import ssl
import websockets
import traceback
import json
import time
import httpx
import datetime
import string




# r : 5 = moder
# r : 1 = user
# r : 6 = Admin


logging.basicConfig(level=logging.INFO)
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.75 Safari/537.36"
client = httpx.AsyncClient(headers={"user-agent":user_agent})
# logger = logging.getLogger('websockets')
# logger.setLevel(logging.DEBUG)
TOKEN = 'JWT eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MTkxNDAwMiwiaWF0IjoxNjQ5Mjc4MTQyLCJleHAiOjE2NTAxNDIxNDJ9.EINacQZl3gU2ao5OhFacWaCCUapor9t4cY0Gh6qK2yo'
ADMINS = [5,6]
PROMO_URL = 'https://api.csgorun.run/discount'
MEDKIT_URL = 'https://api.csgorun.run/use-medkit'
EXCHANGE_URL = 'https://api.csgorun.run/marketplace/exchange-items'
prev_crashes =  []
inventory = []
cur_balance = '0.00'

message_2 = """
{"method":1,"params":{"channel":"u-noty#1914002"},"id":2}
{"method":1,"params":{"channel":"online"},"id":3}
{"method":1,"params":{"channel":"game"},"id":4}
{"method":1,"params":{"channel":"bets"},"id":5}
{"method":1,"params":{"channel":"u-ub#1914002"},"id":6}
{"method":1,"params":{"channel":"user-bet#1914002"},"id":7}
{"method":1,"params":{"channel":"lottery"},"id":8}
{"method":1,"params":{"channel":"u-#1914002"},"id":9}
{"method":1,"params":{"channel":"u-i#1914002"},"id":10}
{"method":1,"params":{"channel":"noty#1914002"},"id":11}
{"method":1,"params":{"channel":"sound#1914002"},"id":12}
{"method":1,"params":{"channel":"withdraw-gift#1914002"},"id":13}
{"method":1,"params":{"channel":"c-ru"},"id":14}
{"method":1,"params":{"channel":"medkit"},"id":15}
"""

def timer(func):
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        time_exec = end - start
        print(f"{func.__name__}: {time_exec:.3f}")
        return result
    return wrapper

def timer_async(func):
    async def wrapper(*args, **kwargs):
        start = time.time()
        result = await func(*args, **kwargs)
        end = time.time()
        time_exec = end - start
        print(f"{func.__name__}: {time_exec:.3f}   {datetime.datetime.now()}")
        return result
    return wrapper



@timer_async
async def get_inv():
    global inventory
    response = await client.get(url='https://api.csgorun.run/current-state?montaznayaPena=null',headers={'authorization': TOKEN})
    inventory = []
    for item in response.json()['data']['user']['items']:
        inventory.append(item['id'])
    return inventory

@timer_async
async def check_promo(msg):
    p = False
    if len(msg) >= 8 and len(msg) <= 12: 
        p = True
        for sym in msg:
            if not sym.isdigit() and sym not in string.ascii_lowercase:
                p = False
    if p == True:
        logging.INFO(f"promo: {msg}\a")

# @timer_async
# async def use_promo(promo):
#     try:
#         response = await client.post(url=PROMO_URL,json={'code':promo,'token':'null'},headers={'authorization':TOKEN})
#         logging.info(f'{promo} promo sent!!!! \a')
#         if response.status_code == httpx.codes.OK:
#             logging.info('+0.25')
#         else:
#             logging.info(f'promik gavno {response.text(),response.json()}')
#     except:
#         traceback.print_exc()

@timer_async
async def inv_header(msg):
    global inventory
    for added in msg['result']['data']['data']['newItems']:
        inventory.append(added['id'])
    for removed in msg['result']['data']['data']['removeItemIds']:
        inventory.remove(removed)
    logging.info(f'inventory is {inventory}')

@timer_async
async def win_header(msg):
    global cur_balance
    global inventory
    cur_balance = msg['result']['data']['data']['balance']
    inventory.append(msg['result']['data']['data']['userItem']['id'])
    logging.info(f'inventory is {inventory}')
    logging.info(f'balance is {cur_balance}')    

@timer_async
async def balance_header(msg):
    global cur_balance
    cur_balance = msg['result']['data']['data']['balance']
    logging.info(f'balance is {cur_balance}')

@timer_async
async def make_bet(cost,crush):
    start = time.time()
    wish_id = [await choose_wish(cost)]
    inv = [await exchange(wish_id)]
    await asyncio.sleep(2)
    response = await client.post(url='https://api.csgorun.run/make-bet',json={'userItemIds':inv,'auto':'1.20'},headers={'authorization':TOKEN})
    tries = 0
    time_left = time.time() - start
    while not response.status_code == httpx.codes.OK and tries < 10 and time_left < 15:    
        logging.info(f'bet isnt made, code {response.text},trying again in 1,try:{tries}')
        response = await client.post(url='https://api.csgorun.run/make-bet',json={'userItemIds':inv,'auto':crush},headers={'authorization':TOKEN})
        tries += 1
        time_left = time.time() - start
        await asyncio.sleep(1)
    if response.status_code == httpx.codes.OK and response.json()['success']:
        logging.info(f"bet made, success = {response.json()['success']}, tries: {tries}")
    else:
        logging.info(f'vse huinya(((( T_T {time_left}')
        exit(1)

@timer_async
async def choose_wish(cost):
    timest = time.time()
    response = await client.get(url = "https://cloud.this.team/csgo/items.json?v=1638190309928")
    logging.info(f'request was made for {time.time()-timest}')
    if response.status_code == httpx.codes.OK:
        costs = [cost-0.01*i for i in range(150)]
        items = {}
        for el in response.json()['data']:
            if cost >= el[6] > cost-1.5:
                items[el[6]] = el[0]
        for cst in costs:
            if items.get(cst):
                logging.info(f'wish id,cost: {items[cst],cst}')
                return items[cst]
        logging.info(f'wish code: {response}, no vse huinya')
        exit()
    else:
        logging.info(f'wish code: {response}')

@timer_async
async def exchange(wish_id):
    global inventory
    try:
        i = 0
        response = await client.post(url=EXCHANGE_URL,json={'userItemIds':inventory,'wishItemIds':wish_id},headers={'authorization':TOKEN})
        if response.status_code == httpx.codes.OK:
            logging.info(f'changed, {i} try')
            return response.json()['data']['userItems']['newItems'][0]['id']
        else:
            inventory = await get_inv()
            for i in range(1,5):
                response = await client.post(url=EXCHANGE_URL,json={'userItemIds':inventory,'wishItemIds':wish_id},headers={'authorization':TOKEN}) 
                if response.status_code == httpx.codes.OK:
                    logging.info(f'changed, {i} try')
                    return response.json()['data']['userItems']['newItems'][0]['id']
                else:
                    logging.info(f'change is not success {response.text,inventory}, {i} try in 1')
    except:
        traceback.print_exc()

@timer_async
async def use_medkit():
    try:
        await asyncio.sleep(2)
        response = await client.post(url=MEDKIT_URL,headers={'authorization':TOKEN})
        if response.status_code == httpx.codes.OK:
            logging.info('medkit used')
        else:
            logging.info('medkit didnt used')
    except:
        traceback.print_exc()

@timer_async
async def consumer_handler(websocket):
    async for message in websocket:
        for line in message.split('\n'):
            if len(line) > 10:
                # logging.info(f'{len(asyncio.all_tasks())}')
                asyncio.create_task(check_message(line))

@timer_async
async def consume(message2,hostname: str,port: int) -> None:
    message1 = json.dumps({"params":{"token":await get_started()},"id":1})
    websocket_resource_url = f"wss://{hostname}:{port}/connection/websocket"
    while True:
        async with websockets.connect(websocket_resource_url,ssl = ssl._create_unverified_context(),extra_headers = {'user-agent':user_agent}) as websocket:
            try:
                await websocket.send(message1)
                await websocket.recv()
                await websocket.send(message2)
                await websocket.recv()
                await consumer_handler(websocket)
            except websockets.ConnectionClosed:
                traceback.print_exc()
                exit()

# @timer_async
async def check_message(msg: str) -> None:
    msg = json.loads(msg)
    try:
        channel = msg['result']['channel']
        if channel == "c-ru":
            # if msg['result']['data']['data']['p']['u'] == type({1:1}) and msg['result']['data']['data']['p']['u'].get('r'):
            #     if msg['result']['data']['data']['p']['u']['r'] in ADMINS:
            #         await check_promo(msg['result']['data']['data']['p']['c'])
            pass
        elif channel == "game":
            if msg['result']['data']['data']['type'] == 'c':
                await check_crush(msg)
        elif channel == "u-#1914002":
            await balance_header(msg)
        elif channel == "u-i#1914002":
            await inv_header(msg)
        elif channel == "u-ub#1914002":
            await win_header(msg)
        elif channel == 'medkit':
            await use_medkit()
    except:
        logging.info(f'pizdec: {msg} {datetime.datetime.now()}')
        traceback.print_exc()

@timer_async
async def check_crush(msg):
    global inventory
    global prev_crashes
    global cur_balance
    crush = msg['result']['data']['data']['c']
    for i in range(len(prev_crashes)-1,0,-1):
        prev_crashes[i] = prev_crashes[i-1]
    prev_crashes[0] = crush
    if max(prev_crashes[:2]) < 1.20 and (cur_balance >= 6 or inventory):
        await make_bet(6,'1.20')
    elif random.randint(1,20) == 6:
        await make_bet(0.20,'1.05')
        

@timer_async
async def get_started():
    global prev_crashes
    global cur_balance
    global inventory
    try:
        response = await client.get(url='https://api.csgorun.run/current-state?montaznayaPena=null',headers={'authorization': TOKEN})
        if response.status_code == httpx.codes.OK:
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
    try:
        # logger.addHandler(logging.StreamHandler())
        # TOKEN = input('JWT eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MTc3ODcsImlhdCI6MTYzODExMzk1NywiZXhwIjoxNjM4OTc3OTU3fQ.mYGvyrnZqnPEcM5sDv6Pln1qTu892QDlN0ziMIOu2oo  ')
        while True:
            try:
                # loop = asyncio.get_event_loop()
                # loop.run_until_complete(consume(message2=message_2,hostname='ws.csgorun.run',port=443))
                # loop.close()
                asyncio.run(consume(message2=message_2,hostname='ws.csgorun.run',port=443))
                logging.info('vsyo govno')
                client.aclose()
                client = httpx.AsyncClient()
            except:
                traceback.print_exc()
    finally:
        client.close()