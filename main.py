import requests
import json
import re
import sys
from datetime import datetime
from pytimekr import pytimekr
from PyQt5 import QtCore, QtGui, QtWidgets

anniversary = {'Jan': {'17': '마틴루터킹 데이'}, 'Feb': {'1': '설날', '13': '수퍼볼 선데이', '14': '발렌타인데이', '21': '프레지던트데이'}, \
               'Mar': {'13': '써머타임시작', '17': '성패트릭스데이'}, 'Apr': {'1': '만우절', '12': '부활절', '22': '지구의날'},
               'May': {'10': '마더스데이', '25': '메모리얼데이'}, \
               'Jun': {'21': '파더스 데이'}, 'Jul': {'4': '독립기념일'}, 'Aug': {'1': '개학시즌 세일'}, 'Sep': {'7': '노동자의 날'},
               'Oct': {'31': '할로윈 데이'}, \
               'Nov': {'11': '재향군인의 날', '25': '블랙프라이데이', '28': '사이버먼데이'},
               'Dec': {'17': '슈퍼새터데이', '25': '크리스마스', '26': '박싱데이', '31': '송년의 날'}}

mon_key_list = list(anniversary.keys())


def search(word):
    url = "https://amazon-product-scraper5.p.rapidapi.com/search/" + word

    querystring = {"api_key": "d1a8234e072f8b7503c43956aa11e281"}

    headers = {
        "X-RapidAPI-Key": "2f32946690msh9ce3185b4d06d00p12d7d3jsnc9e0df35093d",
        "X-RapidAPI-Host": "amazon-product-scraper5.p.rapidapi.com"
    }

    response = requests.request("GET", url, headers=headers, params=querystring)
    result_str = response.json()['results'][0]['url']
    pattern = re.compile("[dp/]+\w{10}|[dp/]+\w{13}")

    re_value = pattern.findall(result_str)[0]
    return re_value[4:]


def priceTracking(asin):
    # asin은 string 값
    url = "https://price-tracking-tools.p.rapidapi.com/camelizer/get-prices"

    querystring = {"asin": asin, "locale": "us"}

    headers = {
        "X-RapidAPI-Key": "2f32946690msh9ce3185b4d06d00p12d7d3jsnc9e0df35093d",
        "X-RapidAPI-Host": "price-tracking-tools.p.rapidapi.com"
    }

    response = requests.request("GET", url, headers=headers, params=querystring)

    return response.json()


def getExchangeRate(date):
    date_list = date.split(' ')
    day = int(date_list[1])

    date = date_list[2] + '-' + (str(mon_key_list.index(date_list[0]) + 1)).zfill(2) + '-' + str(day)

    # AP01 => 환율 AP02 => 대출금리 AP03 => 국제금리
    url = "https://www.koreaexim.go.kr/site/program/financial/exchangeJSON"

    param = {
        'authkey': "uKfAxFx0mB9oKnaa8SHT55pzPBr2oWdz",
        'searchdate': date,
        'data': 'AP01'
    }

    req = requests.get(url, param)
    json_data = req.json()

    if len(json_data) == 1:
        print("사용량초과")
        return 0
    elif len(json_data) == 0:
        # print("주말")
        return 0

    # 22번째가 미국 달러, DEAL_BAS_R 이게 매매 기준율
    json_dollar = json_data[22]

    exchange_dollar = json_dollar.get('deal_bas_r')

    # 성공 1, 코드 오류 2, 인증코드 오류 3, 제한 초과 4
    req_result = json_dollar.get('result')

    exchange_dollar = exchange_dollar.replace(',', '')
    exchange_dollar = float(exchange_dollar)
    return exchange_dollar

def saleInfo(date):
    ret_list = []
    is_on_sale = False
    mon = date.split(' ')[0][0:3]
    day = date.split(' ')[1]
    key = "none"
    sale_days = list(anniversary[mon].keys())

    # 해당 날짜가 세일기간인지?
    if day in sale_days:
        for i in sale_days:
            if (day == i):
                key = i
                ret_list.append(f"현재 진행중인 세일 행사 : {anniversary[mon][key]}")
                is_on_sale = True
    else:
        ret_list.append("현재 진행중인 세일 없음")
    ret_list.append('-' * 24)

    # 다음 세일은 언제?
    ret_list.append('*3개월 이내 세일 목록*')
    ret_list.append('-' * 24)
    for i in sale_days:
        if (day < i):
            key = i
            ret_list.append(f"{mon_key_list.index(mon) + 1}월 {key}일 {anniversary[mon][key]}")

    for n in range(1, 4):
        ret_list.append(' ')
        next_mon_index = (mon_key_list.index(mon) + n) % 12
        next_mon = mon_key_list[next_mon_index]
        next_mon_day = '1'
        sale_days = list(anniversary[next_mon].keys())
        for i in sale_days:
            if (next_mon_day <= i):
                key = i
                ret_list.append(f"{mon_key_list.index(next_mon) + 1}월 {key}일 {anniversary[next_mon][key]}")
    return ret_list, is_on_sale

def getStdDev(date):
    holiday_list = pytimekr.holidays()
    holiday = []

    date_list = date.split(' ')
    mon = mon_key_list.index(date_list[0])
    recent_ex = [0, 0, 0, 0, 0, 0]
    avg = 0

    for i in range(0, 6):
        # 최근 4개월 이내가 연도가 바뀌는 경우 적용
        year = int(date_list[2])
        day = int(date_list[1])
        if (mon - i >= 0):
            mon_index = (mon - i) % 12
        else:
            mon_index = (12 + (mon - i)) % 12
            year = int(date_list[2]) - 1

        # 주말, 공휴일 삭제
        tmp_date = "-".join([str(year), str(mon_index + 1).zfill(2), str(day)])
        tmp_day = day
        while 1:
            if tmp_date not in holiday and datetime(year, mon_index + 1, tmp_day).weekday() < 4:
                break
            if (day >= 15):
                tmp_day = tmp_day - 2
            elif (day < 15):
                tmp_day = tmp_day + 2
            tmp_date = "-".join([str(year), str(mon_index + 1).zfill(2), str(tmp_day)])
        # 환율
        exchange_date = mon_key_list[mon_index] + ' ' + str(tmp_day) + ' ' + str(year)
        tmp = getExchangeRate(exchange_date)
        # 공휴일, 주말을 제외한 비영업일은 알 수 없으므로 제외
        if (tmp != 0):
            recent_ex[i] = tmp
        avg = avg + tmp

    avg = avg / len(recent_ex)
    fluctuation = 0
    for i in recent_ex:
        fluctuation = fluctuation + (avg - i) ** 2

    # print(recent_ex)
    return fluctuation, avg

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(386, 438)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")

        self.productNameLine = QtWidgets.QLineEdit(self.centralwidget)
        self.productNameLine.setGeometry(QtCore.QRect(80, 10, 201, 21))
        self.productNameLine.setObjectName("productNameLine")

        self.priceText = QtWidgets.QTextBrowser(self.centralwidget)
        self.priceText.setGeometry(QtCore.QRect(260, 40, 121, 261))
        self.priceText.setObjectName("priceText")

        self.productLabel = QtWidgets.QLabel(self.centralwidget)
        self.productLabel.setGeometry(QtCore.QRect(10, 10, 61, 21))
        self.productLabel.setObjectName("productLabel")

        self.inputButton = QtWidgets.QPushButton(self.centralwidget)
        self.inputButton.setGeometry(QtCore.QRect(290, 10, 75, 23))
        self.inputButton.setObjectName("inputButton")
        self.inputButton.setCheckable(True)
        self.inputButton.clicked.connect(self.button_event)

        self.saleText = QtWidgets.QTextBrowser(self.centralwidget)
        self.saleText.setGeometry(QtCore.QRect(80, 40, 171, 261))
        self.saleText.setObjectName("saleText")

        self.saleLabel = QtWidgets.QLabel(self.centralwidget)
        self.saleLabel.setGeometry(QtCore.QRect(10, 40, 71, 21))
        self.saleLabel.setObjectName("saleLabel")

        self.resultText = QtWidgets.QTextBrowser(self.centralwidget)
        self.resultText.setGeometry(QtCore.QRect(10, 310, 371, 121))
        self.resultText.setObjectName("resultText")

        MainWindow.setCentralWidget(self.centralwidget)
        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.productLabel.setText(_translate("MainWindow", "상품 이름 :"))
        self.inputButton.setText(_translate("MainWindow", "입력"))
        self.saleLabel.setText(_translate("MainWindow", "행사 정보 :"))


    def button_event(self):
        self.inputButton.toggle()
        self.saleText.clear()
        self.priceText.clear()
        self.resultText.clear()
        product = self.productNameLine.text()
        self.productNameLine.clear()

        aasin = search(product)

        price = priceTracking(aasin)


        product_name = price["title"]
        self.priceText.append(f"상품정보 : {product_name}")
        self.priceText.append('-'*15)

        # 현재 날짜 세일기간 확인
        cur_date = datetime.now()
        cur_date = cur_date.strftime('%b %d %Y')


        # 현재 가격(환율 적용)
        cur_price = price["last_price"]["price_amazon"] / 100
        cur_exchange = getExchangeRate(cur_date)
        self.priceText.append(f'현재가 : {cur_price}달러')
        self.priceText.append(f'현재가 : {int(cur_price * cur_exchange)}원')
        self.priceText.append(f"환율 : {cur_exchange}")
        self.priceText.append('-' * 15)

        # 가장 높을 때 가격(환율 적용)
        highest_price = price["highest_pricing"]["price_amazon"]["price"] / 100
        highest_date = price["highest_pricing"]["price_amazon"]["created_at"].replace(',', '')
        highest_exchange = getExchangeRate(highest_date)
        self.priceText.append(f'최고가 : {highest_price}달러')
        self.priceText.append(f'최고가 : {int(highest_price * highest_exchange)}원')
        self.priceText.append(f"환율 : {highest_exchange}")
        self.priceText.append('-' * 15)

        # 가장 낮을 때 가격(환율 적용)
        lowest_price = price["lowest_pricing"]["price_amazon"]["price"] / 100
        lowest_date = price["lowest_pricing"]["price_amazon"]["created_at"].replace(',', '')
        lowest_exchange = getExchangeRate(lowest_date)
        self.priceText.append(f'최저가 : {lowest_price}달러')
        self.priceText.append(f'최저가 : {int(lowest_price * lowest_exchange)}원')
        self.priceText.append(f"환율 : {lowest_exchange}")
        self.priceText.append('-' * 15)

        texts, is_on_sale = saleInfo(cur_date)
        for i in texts:
            self.saleText.append(i)


        high_cur_diff = abs(cur_price - highest_price)  # 최고가-현재가
        low_cur_diff = abs(cur_price - lowest_price)  # 최저가-현재가
        high_low_diff = high_cur_diff - low_cur_diff

        if high_low_diff <= 0:  # 현재가가 최고가에 근접
            if is_on_sale:
                self.resultText.append("현재 진행중인 행사는 존재하지만 해당상품은 현재 할인을 하고 있지 않을 가능성이 높습니다.")
            else:
                self.resultText.append("현재 진행중인 행사가 없으며 해당상품은 현재 할인중이 아닙니다.")
        elif high_low_diff > 0:  # 현재가가 최저가에 근접
            if is_on_sale:
                self.resultText.append("해당 상품이 현재 세일을 진행중일 가능성이 높으며 구매를 추천드립니다.")
            else:
                self.resultText.append("현재 진행중인 세일은 없지만 합리적인 가격이라 구매해도 손해는 아닙니다.")

        self.resultText.append('-' * 60)

        fluctuation, avg = getStdDev(cur_date)

        if fluctuation >= 40:
            self.resultText.append("최근 환율이 안정적이지 않습니다.")
            if cur_exchange - avg > 0:
                self.resultText.append("환율이 안정적이지 않으니 구매를 고려해보시는 것을 추천드립니다.")
        elif fluctuation < 40:
            self.resultText.append("최근 환율이 안정적입니다.")
        self.resultText.append('-' * 60)





if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())

