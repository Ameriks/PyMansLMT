# coding=utf8

from bs4 import BeautifulSoup
import requests
import time
import urllib
import StringIO
import logging
logging.basicConfig(filename='logs.log',level=logging.DEBUG)

class SessionWHeaders(requests.Session):
    headers2 = {}
    def __init__(self):
        super(SessionWHeaders, self).__init__()
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.95 Safari/537.11',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Encoding': 'gzip,deflate,sdch'}
        self.headers2 = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.95 Safari/537.11',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Encoding': 'gzip, deflate',
            'X-Requested-With': 'XMLHttpRequest'}


class PyMansLMT:
    def __init__(self, username, password):
        self.username = username
        self.password = password

        self.login_count = 0
        self.login()

    def login(self):
        current_timestamp = int(time.time() * 1000)
        self.login_count += 1
        self.session = SessionWHeaders()

        # Get cookies
        html = self.session.get('https://mans.lmt.lv/lv/auth', verify=False)
        soup = BeautifulSoup(html.text)
        lmt_csrf_name = soup.find('input', {"name": "lmt_csrf_name"}).get("value")
        # We need to get captcha image as LMT stores something on their side. If image is not retrieved, then cannot loggin.
        #captchaURL = soup.find("span", {"class": "capcha"}).find("img").get("src")
        #captchaIMG = self.session.get('https://mans.lmt.lv%s' % (captchaURL))
        # Check if we need to decode captcha
        self.session.headers2.update({"lmt_csrf_name": lmt_csrf_name})
        # self.session.headers2.update({"lmt_csrf_name": lmt_csrf_name})
        xml_without_captcha = self.session.post('https://mans.lmt.lv/lv/auth/check-auth-code', data={'lmt_csrf_name': lmt_csrf_name, 'login-number': self.username}, verify=False, headers=self.session.headers2)
        #need_captcha = False  # TODO: Fix this

        post_params = {'lmt_csrf_name': lmt_csrf_name, 'login-name': self.username, 'login-pass': self.password, 'login-code': ''}
        #if need_captcha:
        #    print "DECODING CAPTCHA"
        #    self.dbc.get_balance()
        #    captchaFile = StringIO.StringIO()
        #    captchaFile.write(captchaIMG.content)
        #    captchaFile.seek(0)
        #    captcha = self.dbc.decode(captchaFile)
        #    post_params['code'] = captcha["text"]

        html = self.session.post('https://mans.lmt.lv/lv/auth/login', data=post_params, verify=False, headers=self.session.headers2)
        soup = BeautifulSoup(html.text)

        if html.json().get('success'):
            html = self.session.post('https://mans.lmt.lv%s?_=%i' % (html.json().get('step'), current_timestamp) , data=post_params, verify=False, headers=self.session.headers2)
            if html.json().get('success'):
                html = self.session.post('https://mans.lmt.lv%s?_=%i' % (html.json().get('step'), current_timestamp) , data=post_params, verify=False, headers=self.session.headers2)
                if html.json().get('redirect'):
                    html = self.session.get('https://mans.lmt.lv%s' % html.json().get('redirect'), verify=False)
                    return True
                else:
                    logging.error('Failed to do something: ' + unicode(html.content))
                    raise Exception("Failed to login 1")
            else:
                logging.error('Failed to do something: ' + unicode(html.content))
                raise Exception("Failed to login 2")
        else:
            logging.error('Failed to do something: ' + unicode(html.content))
            raise Exception("Failed to login 3")
        raise Exception("Failed to login")
        # TODO: Rebuild this all.
        if not soup.find("div", {"class": "lmterr"}):
            time.sleep(3)  # Need to sleep 3 secs as LMT website script have such sleep as well. They are gathering some data.
            html = self.session.get('https://mans.lmt.lv/lv/icenter/info.php', verify=False)
            soup = BeautifulSoup(html.text)
            if soup.find("h1") and (soup.find("h1").text == u'Nor\u0113\u0137inu inform\u0101cija' or soup.find("h1").text == u'Inform\xc4\x81cijas sagatavo\xc5\xa1ana'):
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
