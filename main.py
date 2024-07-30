import requests
import random
import string
import time
import re
import logging
import threading

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_proxies(proxy_file="proxies.txt"):
    """Load proxies from a file."""
    with open(proxy_file, "r") as file:
        proxies = file.readlines()
    return [proxy.strip() for proxy in proxies]

def get_random_proxy(proxies):
    """Get a random proxy from the list."""
    proxy = random.choice(proxies)
    return {
        "http": f"http://{proxy}",
        "https": f"http://{proxy}"
    }

def generate_random_string(length=10):
    """Generate a random string of lowercase letters and digits."""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def get_valid_domain(proxy):
    """Fetch a valid email domain from the mail.tm API."""
    try:
        response = requests.get("https://api.mail.tm/domains", proxies=proxy)
        response.raise_for_status()
        domains = response.json()['hydra:member']
        return domains[0]['domain']  # Use the first valid domain
    except requests.RequestException as e:
        logging.error(f"Failed to get valid domain: {e}")
        raise

def get_temp_email(proxy):
    """Generate a temporary email address and return the email details."""
    try:
        valid_domain = get_valid_domain(proxy)
        email_address = generate_random_string() + "@" + valid_domain
        password = generate_random_string(12)
        
        # Register a new account with the valid domain
        response = requests.post("https://api.mail.tm/accounts", json={
            "address": email_address,
            "password": password
        }, proxies=proxy)
        response.raise_for_status()
        email_data = response.json()
        
        # Login to get the access token
        login_response = requests.post("https://api.mail.tm/token", json={
            "address": email_data['address'],
            "password": password
        }, proxies=proxy)
        login_response.raise_for_status()
        login_data = login_response.json()
        
        return email_data['address'], email_data['id'], login_data['token'], password
    except requests.RequestException as e:
        logging.error(f"Failed to get temporary email: {e}")
        raise

def get_verification_link(token, proxy):
    """Retrieve the verification link from the temporary email inbox."""
    verification_link = None
    attempts = 0
    headers = {
        'Authorization': f'Bearer {token}'
    }
    while not verification_link and attempts < 20:  # Try 20 times
        try:
            logging.info(f"Attempt {attempts+1}: Checking for verification email...")
            response = requests.get("https://api.mail.tm/messages", headers=headers, proxies=proxy)
            response.raise_for_status()
            emails = response.json()['hydra:member']
            
            for email in emails:
                if "verify your email address" in email['intro'].lower() or "verify" in email['intro'].lower():
                    email_response = requests.get(f"https://api.mail.tm/messages/{email['id']}", headers=headers, proxies=proxy)
                    email_response.raise_for_status()
                    email_text = email_response.json()['text']
                    verification_link = extract_verification_link(email_text)
                    if verification_link:
                        logging.info(f"Verification link found: {verification_link}")
                        return verification_link
            
            attempts += 1
            time.sleep(10)  # Wait for a while before checking again
        except requests.RequestException as e:
            logging.error(f"Failed to get emails: {e}")
            attempts += 1
            time.sleep(10)  # Wait for a while before checking again
    
    if not verification_link:
        raise Exception("Failed to get verification link")
    return verification_link

def extract_verification_link(email_body):
    """Extract the verification link from the email body."""
    link_match = re.search(r'https://w9y07nr4\.r\.us-east-1\.awstrack\.me/L0/https:%2F%2Fwww\.kashbets\.io%2Fredirect-app\.html%3Faction=verifyemail%26token=[^\s"\'<>]+%26loginName=[^\s"\'<>]+', email_body)
    if not link_match:
        link_match = re.search(r'https://www\.kashbets\.io/account/verify-email\?token=[^\s"\'<>]+&loginName=[^\s"\'<>]+', email_body)
    if not link_match:
        link_match = re.search(r'https://w9y07nr4\.r\.us-east-1\.awstrack\.me/[^\s"\'<>]+', email_body)
    link = link_match.group(0) if link_match else None
    if link and link.endswith(']'):
        link = link[:-1]
    return link

def verify_email_with_token(token, login_name, proxy):
    """Directly verify email using token and login name."""
    headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'en-US,en;q=0.9',
        'content-type': 'application/json',
        'origin': 'https://www.kashbets.io',
        'priority': 'u=1, i',
        'referer': 'https://www.kashbets.io/',
        'sec-ch-ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'cross-site',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
        'webcode': 'IND91',
    }

    json_data = {
        'token': token,
        'loginName': login_name,
    }

    try:
        response = requests.post('https://api.t7o0nx6u21m7.net/v1/api/Accounts/verify-email', headers=headers, json=json_data, proxies=proxy)
        response.raise_for_status()
        logging.info("Email verification successful")
        return True
    except requests.RequestException as e:
        logging.error(f"Failed to verify email: {e}")
        return False

def register_kashbets(email, password, proxy):
    """Register a new account on kashbets.io using the provided email and password."""
    headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'en-US,en;q=0.9',
        'content-type': 'application/json',
        'origin': 'https://www.kashbets.io',
        'priority': 'u=1, i',
        'referer': 'https://www.kashbets.io/',
        'sec-ch-ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'cross-site',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
        'webcode': 'IND91',
    }

    json_data = {
        'phone': None,
        'verificationCode': None,
        'loginName': generate_random_string(),
        'email': email,
        'password':  password,
        'acceptTerms': True,
        'acceptMarketingTerms': True,
        'referralCode': None,
        'inviteCode': "dK9HUu",
        'webCode': 'IND91',
        'clickId': None,
        'captcha': '0258',
        'confirmPassword': password,
        'userAgent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
        'IpAddress': '2401:4900:1c29:7ccd:90f9:4053:9687:5de2',
        'appsFlyerId': None,
        'appsFlyerAppId': None,
        'fingerPrint': 2585614624,
    }

    try:
        response = requests.post(
            'https://api.t7o0nx6u21m7.net/v1/api/Accounts/register',
            headers=headers,
            json=json_data,
            proxies=proxy
        )
        
        if response.status_code == 200:
            logging.info("Registration successful!")
            return json_data['loginName']
        else:
            logging.error(f"Failed to register. Status code: {response.status_code}")
            logging.error(f"Response: {response.text}")
            return None

    except requests.exceptions.RequestException as e:
        logging.error(f"An error occurred during registration: {e}")
        return None

def get_invite_bonus_details(proxy, headers, cookies):
    """Fetch the invite bonus details."""
    try:
        response = requests.get('https://api.t7o0nx6u21m7.net/v1/api/Bonus/invite-detail', headers=headers, cookies=cookies, proxies=proxy)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logging.error(f"Failed to fetch invite bonus details: {e}")
        return None

def account_creation_process(proxy):
    """Handle the entire account creation and verification process."""
    try:
        # Step 1: Generate a temporary email
        random_email, account_id, token, password = get_temp_email(proxy)
        logging.info(f"Temporary email obtained: {random_email}, ID: {account_id}")

        # Step 2: Register on kashbets.io
        login_name = register_kashbets(random_email, password, proxy)
        if login_name:
            # Step 3: Get the verification link from the email
            verification_link = get_verification_link(token, proxy)
            logging.info(f"Verification link obtained: {verification_link}")

            # Step 4: Extract token and loginName from the verification link
            logging.info(f"Verification link: {verification_link}")
            match = re.search(r'token=([^\s&]+)%26loginName=([^\s&/]+)', verification_link)
            if match:
                token = match.group(1)
                login_name = match.group(2)
                logging.info(f"Extracted token: {token}")
                logging.info(f"Extracted loginName: {login_name}")

                # Step 5: Directly verify the email using the extracted token and loginName
                success = verify_email_with_token(token, login_name, proxy)
                if success:
                    logging.info("Account verified successfully!")
                    with open("account.txt", "a") as file:
                        file.write(f"Email: {random_email}, Password: {password}\n")
                    
                    # Step 6: Make the POST request to spin the invite bonus
                    cookies = {
                        'refreshToken': 'A28EB819A53C7D719C154C4C7329DF3B7A9355ED60A4750446BB2FE4E897D7095575D99E2BD8D8F9',
                    }

                    headers_options = {
                        'accept': '*/*',
                        'accept-language': 'en-US,en;q=0.9',
                        'access-control-request-headers': 'authorization,webcode',
                        'access-control-request-method': 'POST',
                        'origin': 'https://www.kashbets.io',
                        'priority': 'u=1, i',
                        'referer': 'https://www.kashbets.io/',
                        'sec-fetch-dest': 'empty',
                        'sec-fetch-mode': 'cors',
                        'sec-fetch-site': 'cross-site',
                        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
                    }

                    # Send OPTIONS request
                    options_response = requests.options('https://api.t7o0nx6u21m7.net/v1/api/Bonus/spin-invite-bonus', headers=headers_options, proxies=proxy)
                    if options_response.status_code == 200:
                        logging.info("OPTIONS request successful")

                    headers_post = {
                        'accept': 'application/json, text/plain, */*',
                        'accept-language': 'en-US,en;q=0.9',
                        'authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjU0NjU2NyIsIm5iZiI6MTcyMTU0NjQ1MiwiZXhwIjoxNzIxNTQ3MzUyLCJpYXQiOjE3MjE1NDY0NTJ9.c5EXzvdIlYd6hG37GtsDDgEft0Tc-YPLjlvJrnrTi7s',
                        'origin': 'https://www.kashbets.io',
                        'priority': 'u=1, i',
                        'referer': 'https://www.kashbets.io/',
                        'sec-ch-ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
                        'sec-ch-ua-mobile': '?0',
                        'sec-ch-ua-platform': '"Windows"',
                        'sec-fetch-dest': 'empty',
                        'sec-fetch-mode': 'cors',
                        'sec-fetch-site': 'cross-site',
                        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
                        'webcode': 'IND91',
                    }

                    response = requests.post('https://api.t7o0nx6u21m7.net/v1/api/Bonus/spin-invite-bonus', cookies=cookies, headers=headers_post, proxies=proxy)
                    
                    if response.status_code == 200:
                        logging.info("Spin invite bonus successful!")
                        
                        # Fetch and display the invite bonus details
                        invite_bonus_details = get_invite_bonus_details(proxy, headers_post, cookies)
                        if invite_bonus_details:
                            logging.info(f"Invite bonus details: {invite_bonus_details}")
                        else:
                            logging.error("Failed to fetch invite bonus details.")
                    else:
                        logging.error(f"Failed to spin invite bonus. Status code: {response.status_code}")
                        logging.error(f"Response: {response.text}")

                else:
                    logging.error("Account verification failed.")
            else:
                logging.error("Failed to extract token and loginName from the verification link.")
        else:
            logging.error("Registration failed.")

    except Exception as e:
        logging.error(f"An error occurred: {e}")

if __name__ == "__main__":
    try:
        proxies = load_proxies()
        num_threads = int(input("Enter the number of threads to run: "))

        threads = []
        for _ in range(num_threads):
            proxy = get_random_proxy(proxies)
            thread = threading.Thread(target=account_creation_process, args=(proxy,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

    except Exception as e:
        logging.error(f"An error occurred: {e}")
