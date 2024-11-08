import requests
from bs4 import BeautifulSoup


def getParameters():
# URL of the page
    url = 'https://inquiry.mohre.gov.ae/'

    # Request the page
    response = requests.get(url)
    cookies = response.cookies
    cookie_name = next(iter(cookies.keys()))
    cookie_value = cookies[cookie_name]
    html_content = response.text

    # Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')

    # Extract the values
    request_verification_token = soup.find('input', {'name': '__RequestVerificationToken'})['value']
    otp_url = soup.find('input', {'id': 'OTPURL'})['value']
    input_otp = soup.find('label', {'for': 'InputOTP'}).find('span').text.strip()

    # Print the extracted values
    return request_verification_token, otp_url, input_otp, cookie_name, cookie_value
