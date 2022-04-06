import requests
import datetime
import time
import traceback

URL = "https://api.csgorun.run/roulette/state"
JSON = {}
# 3 - золотая
# 2 - зелёный
# 1 - синий
print(f"start")
TIME_SLEEP = 21  
# 1 раунд ровно 1 раз в 21 секунду


def make_noise(n):
    for i in range(n):
        print("\a")
        time.sleep(1)

def main():
    while True:
        try:
            response = requests.get(URL)
            datetime.datetime.now()
            if response.ok:
                print("ok", datetime.datetime.now())
                cnts = {1:0,2:0,3:0}
                flag = False
                history = response.json()["data"]['history']
                history.sort(key = lambda x: list(x.values())[0],reverse = True)
                f = open('mbr.txt','r')
                max_break_l = [int(x) for x in f]
                max_break = 0
                f.close
                for i in range(100): 
                    cnts[history[i]['winnerNumber']] += 1
                    if flag == False and history[i]['winnerNumber'] == 3:
                        flag = True
                        print(i)
                        if i > max_break:
                            max_break = i
                if max_break > max_break_l[4]:
                    for i in range(len(max_break_l)):
                        if max_break_l[i] < max_break:
                            for j in range(len(max_break_l)-1,i,1):
                                max_break_l[j] = max_break_l[j+1]
                            max_break_l[i] = max_break
                            break
                f = open('C:/Users/youtu/Downloads/Telegram Desktop/mbr.txt','w')
                for el in max_break_l:
                    f.write(str(el)+'\n')
                f.close()
                print(f'b-{cnts[1]} g-{cnts[2]} y-{cnts[3]}') 
            else:
                print(f"Error: status_code={response.status_code} text={response.text}")
        except:
            traceback.print_exc()
            
        time.sleep(TIME_SLEEP)


if __name__ == "__main__":
    main()