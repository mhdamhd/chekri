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
    'Origin': 'https://erp.maids.cc',
    'Connection': 'keep-alive',
    'Referer': 'https://erp.maids.cc/',
    'Cookie': '_ga_NNRJWTQKNE=GS1.1.1726817910.1.0.1726817912.0.0.0; _ga=GA1.2.1906044194.1726817911; _gid=GA1.2.3264093.1726817911; _gat_gtag_UA_145005355_1=1; mp_6cede7e71acfcd73af90ddd57dde2ba6_mixpanel=%7B%22distinct_id%22%3A%20%22%24device%3A1920e5e3fa55ae-064768e89e12888-432e2f34-13c680-1920e5e3fa55ae%22%2C%22%24device_id%22%3A%20%221920e5e3fa55ae-064768e89e12888-432e2f34-13c680-1920e5e3fa55ae%22%2C%22%24initial_referrer%22%3A%20%22https%3A%2F%2Ferp.maids.cc%2Fmain.html%22%2C%22%24initial_referring_domain%22%3A%20%22erp.maids.cc%22%2C%22__mps%22%3A%20%7B%7D%2C%22__mpso%22%3A%20%7B%22%24initial_referrer%22%3A%20%22https%3A%2F%2Ferp.maids.cc%2Fmain.html%22%2C%22%24initial_referring_domain%22%3A%20%22erp.maids.cc%22%7D%2C%22__mpus%22%3A%20%7B%7D%2C%22__mpa%22%3A%20%7B%7D%2C%22__mpu%22%3A%20%7B%7D%2C%22__mpr%22%3A%20%5B%5D%2C%22__mpap%22%3A%20%5B%5D%7D; authTokenProduction=eyJhbGciOiJIUzUxMiJ9.eyJ1c2VyIjoiTW9oYW1tYWRNIiwiZGV2aWNlIjoiMTcyNDg0NDYwMjg5NCIsImlhdCI6MTcyNjgxODkzNywiZXhwIjoxNzI2ODI5NzM3fQ.qaGRuRbp6j2cY8JVbg4CZQsjGKAFX1I5hjIpFGrRTOXAntUPtswfOXppgHh3f4zpdyc7ox_E4Y7vPHSGt8HARg',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-site',
    'Priority': 'u=0',
    'TE': 'trailers'
    }
    print("logging in...")

    response = requests.request("POST", url, headers=headers, data=payload)

    if response.status_code == 200:
        # Step 1: Extract the token from the headers
        token = response.headers.get('token')
        token = token.replace("Bearer ", "")

        if token:
            print("Logged in successfully")
        else:
            print("Token not found in response headers.")
    else:
        print(f"Failed to login, status code: {response.status_code}")

    return f"{token}"

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
    return response.text == "\"Validated\""


def getAWP(token):
    url = "https://erpbackendpro.maids.cc/visa/newRequest/tasks?search=&taskName=Create%20Regular%20Offer%20Letter"

    payload = {}
    headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:131.0) Gecko/20100101 Firefox/131.0',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br, zstd',
    'Searchfilter': '',
    'Access-Control-Allow-Origin': '*',
    'Authorization': '',
    'pageCode': 'VisaProcessingPage',
    'Origin': 'https://erp.maids.cc',
    'Connection': 'keep-alive',
    'Referer': 'https://erp.maids.cc/',
    'Cookie': f'authTokenProduction={token}; user=%7B%22loginName%22%3A%22MohammadM%22%7D; isERPAuth=MohammadM',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-site',
    'TE': 'trailers'
    }

    response = requests.request("GET", url, headers=headers, data=payload)

    return response.json()

def awpSearchName(token, name):
    url = f"https://erpbackendpro.maids.cc/visa/newRequest/getTaskHeaders?search={name}"

    payload = {}
    headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:131.0) Gecko/20100101 Firefox/131.0',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br, zstd',
    'Access-Control-Allow-Origin': '*',
    'Authorization': '',
    'pageCode': 'VisaProcessingPage',
    'Origin': 'https://erp.maids.cc',
    'Connection': 'keep-alive',
    'Referer': 'https://erp.maids.cc/',
    # 'Cookie': '_ga=GA1.2.1177104381.1728983484; _ga_NNRJWTQKNE=GS1.1.1728986033.2.1.1728986035.0.0.0; mp_6cede7e71acfcd73af90ddd57dde2ba6_mixpanel=%7B%22distinct_id%22%3A%20%22%24device%3A1928f7247944b7-0b3aa5d9bf3d5b-432f2f35-4f1a0-1928f7247944b7%22%2C%22%24device_id%22%3A%20%221928f7247944b7-0b3aa5d9bf3d5b-432f2f35-4f1a0-1928f7247944b7%22%2C%22%24initial_referrer%22%3A%20%22https%3A%2F%2Ferp.maids.cc%2Fmain.html%22%2C%22%24initial_referring_domain%22%3A%20%22erp.maids.cc%22%2C%22__mps%22%3A%20%7B%7D%2C%22__mpso%22%3A%20%7B%22%24initial_referrer%22%3A%20%22https%3A%2F%2Ferp.maids.cc%2Fmain.html%22%2C%22%24initial_referring_domain%22%3A%20%22erp.maids.cc%22%7D%2C%22__mpus%22%3A%20%7B%7D%2C%22__mpa%22%3A%20%7B%7D%2C%22__mpu%22%3A%20%7B%7D%2C%22__mpr%22%3A%20%5B%5D%2C%22__mpap%22%3A%20%5B%5D%7D; mp_43aa8cf76ee27ec8f80f8e50b23617d3_mixpanel=%7B%22distinct_id%22%3A%20%22%24device%3A1928f7256d44ea-0da4662520ef7f8-432f2f35-4f1a0-1928f7256d44ea%22%2C%22%24device_id%22%3A%20%221928f7256d44ea-0da4662520ef7f8-432f2f35-4f1a0-1928f7256d44ea%22%2C%22%24initial_referrer%22%3A%20%22https%3A%2F%2Ferp.maids.cc%2Flogin.html%22%2C%22%24initial_referring_domain%22%3A%20%22erp.maids.cc%22%2C%22__mps%22%3A%20%7B%7D%2C%22__mpso%22%3A%20%7B%22%24initial_referrer%22%3A%20%22https%3A%2F%2Ferp.maids.cc%2Flogin.html%22%2C%22%24initial_referring_domain%22%3A%20%22erp.maids.cc%22%7D%2C%22__mpus%22%3A%20%7B%7D%2C%22__mpa%22%3A%20%7B%7D%2C%22__mpu%22%3A%20%7B%7D%2C%22__mpr%22%3A%20%5B%5D%2C%22__mpap%22%3A%20%5B%5D%7D; _gid=GA1.2.1847259003.1730107841; authTokenProduction=eyJhbGciOiJIUzUxMiJ9.eyJ1c2VyIjoiTW9oYW1tYWRNIiwiZGV2aWNlIjoiMTcyNDg0NDYwMjg5NCIsImlhdCI6MTczMDEwNzg0NSwiZXhwIjoxNzMwMTE4NjQ1fQ.xgh89Duz5t_YMNlGv8blhTPND-_1eohLGEpIPAs8FSCIBb7g7ZBgzYbMIa8uaXYmQSLoY6I7rL-Ds1My49GyNQ; user=%7B%22loginName%22%3A%22MohammadM%22%7D; isERPAuth=MohammadM',
    'Cookie': f'authTokenProduction={token}; user=%7B%22loginName%22%3A%22MohammadM%22%7D; isERPAuth=MohammadM',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-site',
    'Priority': 'u=0',
    'TE': 'trailers'
    }

    response = requests.request("GET", url, headers=headers, data=payload)

    return response.json()

