import base64
import time
import requests

def login(username, password):
    timestamp = str(int(time.time() * 1000))

    # Format the string as "username:password:timestamp"
    credential_string = f"{username}:{password}:{timestamp}"
    # Encode the string in Base64
    payload = base64.b64encode(credential_string.encode("utf-8")).decode("utf-8")
    payload = f'"{payload}"'
    
    url = "https://erpbackendpro.maids.cc/public/login/jwt"
    headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:130.0) Gecko/20100101 Firefox/130.0',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br, zstd',
    'Content-Type': 'application/json;charset=utf-8',
    'Content-Length': '50',
    'Origin': 'https://erp.maids.cc',
    'Connection': 'keep-alive',
    'Referer': 'https://erp.maids.cc/',
    'Cookie': 'deviceIdProduction=1724844602894; mfaCodeProduction=357549; deviceIdProduction=1730891855619',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-site',
    'Priority': 'u=0'
    }
    print("logging in...")

    response = requests.request("POST", url, headers=headers, data=payload)

    if response.status_code == 200:
        deviceIdProduction = response.headers.get('Set-Cookie').split(';')[0].split('=')[1]
        # Step 1: Extract the token from the headers
        token = response.headers.get('token')
        token = token.replace("Bearer ", "")

        if token:
            print("Logged in successfully")
        else:
            print("Token not found in response headers.")
    else:
        print(f"Failed to login, status code: {response.status_code}")

    return f"{token}", deviceIdProduction

def verifyOtp(token, otp_code):
    url = f"https://erpbackendpro.maids.cc/public/login/validate-totp?code={otp_code}"

    headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:130.0) Gecko/20100101 Firefox/130.0',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br, zstd',
    'Content-Type': 'application/json;charset=utf-8',
    'Origin': 'https://erp.maids.cc',
    'Connection': 'keep-alive',
    'Referer': 'https://erp.maids.cc/',
    'Cookie': f'authTokenProduction={token}',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-site',
    'Priority': 'u=0',
    'TE': 'trailers'
    }

    response = requests.request("POST", url, headers=headers)
    mfaCodeProduction = response.headers.get('Set-Cookie').split(';')[0].split('=')[1]
    return response.text == "\"Validated\"", mfaCodeProduction


def getAWP(token, deviceIdProduction, mfaCodeProduction):
    url = "https://erpbackendpro.maids.cc/visa/newRequest/tasks?search=&taskName=Create%20Regular%20Offer%20Letter"

    payload = {}
    headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:131.0) Gecko/20100101 Firefox/131.0',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br, zstd',
    'Searchfilter': '',
    'Access-Control-Allow-Origin': '*',
    'Authorization': f'{token}',
    'pageCode': 'VisaProcessingPage',
    'Origin': 'https://erp.maids.cc',
    'Connection': 'keep-alive',
    'Referer': 'https://erp.maids.cc/',
    'Cookie': f'deviceIdProduction={deviceIdProduction}; mfaCodeProduction={mfaCodeProduction}; authTokenProduction={token};',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-site',
    'TE': 'trailers'
    }
    response = requests.request("GET", url, headers=headers, data=payload)

    return response.json()

def awpSearchName(token, deviceIdProduction, mfaCodeProduction, name):
    url = f"https://erpbackendpro.maids.cc/visa/newRequest/getTaskHeaders?search={name}"

    payload = {}
    headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:131.0) Gecko/20100101 Firefox/131.0',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br, zstd',
    'Access-Control-Allow-Origin': '*',
    'Authorization': f'{token}',
    'pageCode': 'VisaProcessingPage',
    'Origin': 'https://erp.maids.cc',
    'Connection': 'keep-alive',
    'Referer': 'https://erp.maids.cc/',
    'Cookie': f'deviceIdProduction={deviceIdProduction}; mfaCodeProduction={mfaCodeProduction}; authTokenProduction={token};',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-site',
    'Priority': 'u=0',
    'TE': 'trailers'
    }
    response = requests.request("GET", url, headers=headers, data=payload)

    return response.json()