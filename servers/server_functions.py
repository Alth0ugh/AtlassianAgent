import base64

def convert_credentials(mail: str, token: str) -> str:
    """
    Converts credentials into base64.
    
    Parameters:
        mail (str): User email.
        token (str): Atlassian ID token.

    Returns:
        str: Base64 encoded mail and token.
    """
    credentials = f"{mail}:{token}"
    string_bytes = credentials.encode("utf-8")
    base64_bytes = base64.b64encode(string_bytes)
    return base64_bytes.decode("utf-8")

def get_headers(credentials: str) -> dict[str, str]:
    """
    Creates dictionary with HTTP headers.

    Parameters:
        credentials (str): Base64 encoded user credentials.

    Returns:
        Dict: dictionary containing HTTP headers.
    """
    return {"Authorization": f"Basic {credentials}",
        "Accept": "application/json",
        "Content-Type": "application/json"}