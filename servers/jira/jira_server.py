from mcp.server.fastmcp import FastMCP, Context
import requests
import base64
from argparse import ArgumentParser
from jira_create_request import CreateRequest
from server_response import Response
from dataclasses import asdict

parser = ArgumentParser()
parser.add_argument("--host", type=str, help="IP address of the server", default="0.0.0.0")
parser.add_argument("--port", type=int, help="Port on which the server will be running.", default=8050)
parser.add_argument("--space", type=str, help="Name of the Atlassian space.", required=True)
args = parser.parse_args()

credentials = ""

mcp = FastMCP(
    name="JiraServer"
)

@mcp.tool(description="Creates a ticket in Jira. Returns a response object with the following properties: is_error: boolean indicating whether an error occured, error_message: string containing error message if an error occured.")
def create_ticket(ctx: Context, summary: str, description: str, project: str) -> dict:
    request = CreateRequest(project, summary, description)
    headers = {"Authorization": f"Basic {credentials}",
           "Accept": "application/json",
           "Content-Type": "application/json"}
    response = requests.post(f"https://{args.space}.atlassian.net/rest/api/3/issue", data=request.to_json(), headers=headers)
    if response.status_code == 201:
        return asdict(Response(False))
    elif response.status_code == 400:
        return asdict(Response(True, "The request was malformed."))
    elif response.status_code == 401:
        return asdict(Response(True, "User cannot be authenticated."))
    elif response.status_code == 403:
        return asdict(Response(True, "User does not have permissions for this operaiton."))
    elif response.status_code == 422:
        return asdict(Response(True, "Configuration problem prevents execution of this operation."))

if __name__ == "__main__":
    mcp.run(transport="sse")
