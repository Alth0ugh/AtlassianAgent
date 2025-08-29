from argparse import ArgumentParser
from dataclasses import asdict
from typing import Optional
import json

from mcp.server.fastmcp import FastMCP
import requests

from server_functions import (
    convert_credentials,
    get_headers
)
from server_response import Response

parser = ArgumentParser()
parser.add_argument("--space",
                    type=str,
                    help="Name of the Atlassian space.",
                    required=True)
parser.add_argument("--mail",
                    type=str,
                    help="Name of the Atlassian space.",
                    required=True)
parser.add_argument("--token",
                    type=str,
                    help="Name of the Atlassian space.",
                    required=True)
args = parser.parse_args()

mcp = FastMCP(
    name="ConfluenceServer"
)


def get_space_id(name: str) -> Optional[str]:
    """
    Retrieves the ID of the space by the space name.

    Parameters:
        name (str): Name of the space.

    Returns:
        Optional[str]: ID of the space or None.
    """
    credentials = convert_credentials(args.mail, args.token)
    headers = get_headers(credentials)

    response = requests.get(
        f"https://{args.space}.atlassian.net/wiki/api/v2/spaces",
        headers=headers)

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
          A response object with the following properties:
          is_error: boolean indicating whether an error occured,
          error_message: string with error message if an error occured.""")
def create_page(space: str, title: str, content: str) -> str:
    """
    Creates new Confluence page.

    Parameters:
        space (str): Space where the page is located.
        title (str): The title of the page.
        content (str): Text content of the page.

    Returns:
        str: JSON encoded Response object.
    """
    credentials = convert_credentials(args.mail, args.token)
    headers = get_headers(credentials)

    space_id = get_space_id(space)

    if space_id is None:
        return json.dumps(
            asdict(Response(True, "The space could not be found."))
            )

    body = {
        "spaceId": space_id,
        "title": title,
        "body": {
            "representation": "storage",
            "value": content
        }
    }

    response = requests.post(
        f"https://{args.space}.atlassian.net/wiki/api/v2/pages",
        headers=headers,
        data=json.dumps(body)
        )

    if response.status_code != 200:
        return json.dumps(
            asdict(Response(True, "The page could not be created"))
            )
    return json.dumps(
        asdict(Response(False))
        )


@mcp.tool(description="""Searches for pages in the space by the title.

          Parameters:
          space: space where to look for the page
          title: title of the searched page

          Returns:
          A list of page titles and contents.
          In case of error, a response object with the following properties:
          is_error: boolean indicating whether an error occured
          error_message: string containing error message""")
def search_page(space: str, title: str) -> str:
    """
    Searches for a page by its title in a given space.

    Parameters:
        space (str): The space for search.
        title (str): The title of the page.

    Returns:
        str: JSON containing list of pages or Response object if error.
    """
    credentials = convert_credentials(args.mail, args.token)
    headers = get_headers(credentials)

    space_id = get_space_id(space)

    params = {
        "space-id": space_id,
        "title": title,
        "body-format": "storage"
    }

    response = requests.get(
        f"https://{args.space}.atlassian.net/wiki/api/v2/pages",
        headers=headers,
        params=params
        )

    if response.status_code != 200:
        return json.dumps(
            asdict(Response(True, "The page could not be found"))
            )

    results = response.json()["results"]
    if len(results) == 0:
        return json.dumps(
            asdict(Response(True, "The page could not be found"))
            )

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
