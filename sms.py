# coding=utf8

from bs4 import BeautifulSoup
import requests
import time
import urllib
import deathbycaptcha
import StringIO


class SessionWHeaders(requests.Session):
    def __init__(self):
        super(SessionWHeaders, self).__init__()
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.95 Safari/537.11',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Encoding': 'gzip,deflate,sdch'}


class PyMansLMT:
    def __init__(self, username, password, dusername=None, dpassword=None):
        self.username = username
        self.password = password

        self.dbc = deathbycaptcha.SocketClient(dusername, dpassword)

        self.login_count = 0
        self.login()

    def login(self):
        current_timestamp = int(time.time() * 1000)
        self.login_count += 1
        self.session = SessionWHeaders()

        # Get cookies
        html = self.session.get('https://mans.lmt.lv/lv/', verify=False)
        soup = BeautifulSoup(html.text)

        # We need to get captcha image as LMT stores something on their side. If image is not retrieved, then cannot loggin.
        captchaURL = soup.find("span", {"class": "capcha"}).find("img").get("src")
        captchaIMG = self.session.get('https://mans.lmt.lv%s' % (captchaURL))
        # Check if we need to decode captcha
        xml_without_captcha = self.session.post('https://mans.lmt.lv/lv/xml/login_auth.php?%d' % (current_timestamp), data={'check_auth_code': '1', 'msisdn': self.username}, verify=False)
        need_captcha = xml_without_captcha.content == 'false'

        post_params = {'where_login_form': 'manslmt', 'username': self.username, 'password': self.password, 'code': '', 'submit': 'login'}
        if need_captcha:
            print "DECODING CAPTCHA"
            self.dbc.get_balance()
            captchaFile = StringIO.StringIO()
            captchaFile.write(captchaIMG.content)
            captchaFile.seek(0)
            captcha = self.dbc.decode(captchaFile)
            post_params['code'] = captcha["text"]

        html = self.session.post('https://mans.lmt.lv/lv/index.php', data=post_params, verify=False)
        soup = BeautifulSoup(html.text)

        if not soup.find("div", {"class": "lmterr"}):
            time.sleep(3)  # Need to sleep 3 secs as LMT website script have such sleep as well. They are gathering some data.
            html = self.session.get('https://mans.lmt.lv/lv/icenter/info.php', verify=False)
            soup = BeautifulSoup(html.text)
            if soup.find("h1") and (soup.find("h1").text == u'Nor\xc4\x93\xc4\xb7inu inform\xc4\x81cija' or soup.find("h1").text == u'Inform\xc4\x81cijas sagatavo\xc5\xa1ana'):
                return True
            else:
                raise Exception("Error logging in mans.lmt.lv")
        elif soup.find("div", {"class": "lmterr"}).text == u'Nesekm\xc4\xabga autoriz\xc4\x81cija':  # u'Nesekmīga autorizācija':
            raise Exception("Incorrect mans.lmt username or password")
        elif soup.find("div", {"class": "lmterr"}).text == u'Nepareizs kods.' and need_captcha:
            print "Incorrect captcha"
            self.dbc.report(captcha['captcha'])  # Report incorrect captcha

        time.sleep(5)
        if self.login_count > 5:
            raise Exception("Tried to login 5 times.")

        return self.login()

    def send_sms(self, numbers, message, validate=False):
        numbers = list(set(numbers))  # Remove duplicate numbers
        if len(message) == 0 or len(message) > 160:
            raise Exception("Message too long or not set")

        html = self.session.get('https://mans.lmt.lv/lv/sms_group/index.php', verify=False)
        soup = BeautifulSoup(html.text)
        hidden_fields = soup.find("form", {"id": "sms-groups-send"}).findAll("input", {"type": "hidden"})
        post_params = {}
        for inp in hidden_fields:
            post_params[inp.get("name")] = inp.get("value")
        post_params['sms-text'] = message
        post_params['sms-number[]'] = numbers
        if validate:
            post_params['sms-group-preview'] = 'Pārbaudīt'
            post_params['preview'] = "1"
        else:
            post_params['sms-group-send'] = 'Nosūtīt'
            post_params['preview'] = "0"

        html = self.session.post('https://mans.lmt.lv/lv/sms_group/index.php', data=post_params, verify=False)
        soup = BeautifulSoup(html.text)

        incorrect = []

        errors = soup.find("div", {"class": "lmterr"})
        if errors:
            error = errors.text
            if len(error.split(" - ")) == 1:
                incorrect = numbers
                numbers = []
            else:
                incorrect = error.split(" - ")[1][:-1].split(", ")
                for i in incorrect:
                    try:
                        numbers.remove(i)
                    except:
                        pass
        return [numbers, incorrect]
