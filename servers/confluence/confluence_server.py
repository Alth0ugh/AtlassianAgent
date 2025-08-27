from mcp.server.fastmcp import FastMCP
import requests
import base64
from argparse import ArgumentParser
import json
from dataclasses import asdict

parser = ArgumentParser()
parser.add_argument("--space", type=str, help="Name of the Atlassian space.", required=True)
parser.add_argument("--mail", type=str, help="Name of the Atlassian space.", required=True)
parser.add_argument("--token", type=str, help="Name of the Atlassian space.", required=True)
args = parser.parse_args()

mcp = FastMCP(
    name="ConfluenceServer"
)

if __name__ == "__main__":
    mcp.run(transport="stdio")