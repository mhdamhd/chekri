import requests
from datetime import datetime
from getParameters import getParameters


def postRequest(inputData):
    # Get the current date
    today_date = datetime.today()

    # Format the date
    formatted_date = today_date.strftime('%d/%m/%Y')

    request_verification_token, otp_url, input_otp, cookie_name, cookie_value = getParameters()

    url = "https://inquiry.mohre.gov.ae/TransactionInquiry/OnProtectData"

    payload = {'inquiryCode': 'AS',
    'InputData': inputData,
    'Emirates': '000000001',
    'CompCode': '',
    'StartDate': '',
    'EndDate': '',
    'permitType': '0',
    'TransactionNo': '',
    'PersonCode': '',
    'PersonDateOfBirth': formatted_date,
    'OTP': input_otp,
    'OTPURL': otp_url,
    'InputOTP': input_otp,
    'InputLanguge': 'en',
    '__RequestVerificationToken': request_verification_token}
    files=[

    ]
    headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:128.0) Gecko/20100101 Firefox/128.0',
    'Accept': '*/*',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br, zstd',
    'X-Requested-With': 'XMLHttpRequest',
    'Origin': 'https://inquiry.mohre.gov.ae',
    'Connection': 'keep-alive',
    'Referer': 'https://inquiry.mohre.gov.ae/',
    'Cookie': f'{cookie_name}={cookie_value}',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
    'Priority': 'u=0',
    'TE': 'trailers'
    }

    response = requests.request("POST", url, headers=headers, data=payload, files=files)

    return response.text
