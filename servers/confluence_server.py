from mcp.server.fastmcp import FastMCP
import requests
import base64
from argparse import ArgumentParser
import json
from dataclasses import asdict
from server_response import Response

parser = ArgumentParser()
parser.add_argument("--space", type=str, help="Name of the Atlassian space.", required=True)
parser.add_argument("--mail", type=str, help="Name of the Atlassian space.", required=True)
parser.add_argument("--token", type=str, help="Name of the Atlassian space.", required=True)
args = parser.parse_args()

mcp = FastMCP(
    name="ConfluenceServer"
)

def convert_credentials(mail: str, token: str) -> str:
    credentials = f"{mail}:{token}"
    string_bytes = credentials.encode("utf-8")
    base64_bytes = base64.b64encode(string_bytes)
    return base64_bytes.decode("utf-8")

def get_headers(credentials: str) -> dict:
        return {"Authorization": f"Basic {credentials}",
        "Accept": "application/json",
        "Content-Type": "application/json"}

def get_space_id(name: str) -> list | None:
    credentials = convert_credentials(args.mail, args.token)
    headers = get_headers(credentials)

    response = requests.get(f"https://{args.space}.atlassian.net/wiki/api/v2/spaces", headers=headers)

    if response.status_code != 200:
        return None
    spaces = response.json()["results"]
    for space in spaces:
        space_name = space["name"]
        id = space["id"]
        if space_name == name:
            return id

    return None

@mcp.tool(description="""Creates new Confluence page.
          
          Parameters:
          space: name of the space to create the page in
          title: title of the page
          content: text content of the page

          Returns:
           A response object with the following properties: is_error: boolean indicating whether an error occured, error_message: string containing error message if an error occured.""")
def create_page(space: str, title: str, content: str):
    credentials = convert_credentials(args.mail, args.token)
    headers = get_headers(credentials)

    space_id = get_space_id(space)

    if space_id is None:
        return json.dumps(asdict(Response(True, "The space could not be found.")))

    body = {
        "spaceId": space_id,
        "title": title,
        "body": {
            "representation": "storage",
            "value": content
        }
    }

    response = requests.post(f"https://{args.space}.atlassian.net/wiki/api/v2/pages", headers=headers, data=json.dumps(body))

    if response.status_code != 200:
        return json.dumps(asdict(Response(True, "The page could not be created")))
    return json.dumps(asdict(Response(False)))

@mcp.tool(description="""Searches for pages in the space by the title.
          
          Parameters:
          space: space where to look for the page
          title: title of the searched page
          
          Returns:
          A list of page titles and contents.
          In case an error accurs, a response object with the following properties: is_error: boolean indicating whether an error occured, error_message: string containing error message if an error occured.""")
def search_page(space: str, title: str):
    credentials = convert_credentials(args.mail, args.token)
    headers = get_headers(credentials)

    space_id = get_space_id(space)

    params = {
        "space-id": space_id,
        "title": title,
        "body-format": "storage"
    }

    response = requests.get(f"https://{args.space}.atlassian.net/wiki/api/v2/pages", headers=headers, params=params)

    if response.status_code != 200:
        return json.dumps(asdict(Response(True, "The page could not be found")))
    
    results = response.json()["results"]
    if len(results) == 0:
        return json.dumps(asdict(Response(True, "The page could not be found")))
    
    found_pages = []
    for page in results:
        title = page["title"]
        body = page["body"]
        text = ""
        if body is not None:
            text = body["storage"]["value"]
        found_pages.append({"title": title, "text": text})

    return json.dumps(found_pages)

if __name__ == "__main__":
    mcp.run(transport="stdio")