PyMansLMT
=============

This class allows integration with manslmt.lv site to send SMS messages from your number to Latvian phone number.

### Install required libraries:
    pip install BeautifulSoup
    pip install requests

### Create deathbycaptcha account (optional):
This is optional, but script will not be able to login if manslmt will ask to fill captcha. Captcha is asked if password is entered incorrectly at least once.
* [deathbycaptcha](http://www.deathbycaptcha.com/)

### Example:
    from sms import PyMansLMT
    instance = PyMansLMT("PHONE", "PASSWORD", 'DBC_USERNAME', 'DBC_PASSWORD')

Validate phone numbers:
    result = instance.send_sms(['PHONE1','PHONE2','PHONE3'], 'Test message', True)

Send SMS to validated SMS numbers:
    sent = instance.send_sms(result[0], 'Test message')