from mcp.server.fastmcp import FastMCP, Context
import requests
import base64
from argparse import ArgumentParser
from jira_create_request import CreateRequest
from server_response import Response
import json

parser = ArgumentParser()
parser.add_argument("--host", type=str, help="IP address of the server", default="0.0.0.0")
parser.add_argument("--port", type=int, help="Port on which the server will be running.", default=8050)
parser.add_argument("--space", type=str, help="Name of the Atlassian space.", required=True)
args = parser.parse_args()

mcp = FastMCP(
    name="JiraServer"
)

def get_credentials(ctx: Context) -> str | None:
    return ctx.request_context.request.headers.get("authorization") # type: ignore

@mcp.tool(description="Creates a ticket in Jira. Returns a response object with the following properties: is_error: boolean indicating whether an error occured, error_message: string containing error message if an error occured.")
def create_ticket(ctx: Context, summary: str, description: str, project: str) -> str:
    credentials = get_credentials(ctx)
    if credentials is None:
        return json.dumps(Response(True, "No valid credentials were found in the request."))
    
    request = CreateRequest(project, summary, description)
    headers = {"Authorization": f"Basic {credentials}",
           "Accept": "application/json",
           "Content-Type": "application/json"}
    response = requests.post(f"https://{args.space}.atlassian.net/rest/api/3/issue", data=request.to_json(), headers=headers)

    if response.status_code == 201:
        return json.dumps(Response(False))
    elif response.status_code == 400:
        return json.dumps(Response(True, "The request was malformed."))
    elif response.status_code == 401:
        return json.dumps(Response(True, "User cannot be authenticated."))
    elif response.status_code == 403:
        return json.dumps(Response(True, "User does not have permissions for this operaiton."))
    elif response.status_code == 422:
        return json.dumps(Response(True, "Configuration problem prevents execution of this operation."))
    return json.dumps(Response(True, "No valid credentials were found in the request."))
    
@mcp.tool(description="Lists all tickets assigned to the current user. This tools does not need any parameters. Returns a list of issues with key, summary and description of each issue. If error occurs, returns json with the following properties: is_error: boolean indicating whether an error occured, error_message: string containing error.")
def load_tickets(ctx: Context) -> str:
    credentials = get_credentials(ctx)
    if credentials is None:
        return json.dumps(Response(True, "No valid credentials were found in the request."))

    headers = {"Authorization": f"Basic {credentials}",
           "Accept": "application/json",
           "Content-Type": "application/json"}
    response = requests.get("https://agenticspace.atlassian.net/rest/api/3/myself", headers=headers)
    if response.status_code != 200:
        return json.dumps(Response(True, "User not found."))
    
    response = response.json()
    email = response["emailAddress"]

    params = {
        "jql": f'assignee = "{email}" ORDER BY created DESC',
              "fields": "summary, description"
    }

    response = requests.get("https://agenticspace.atlassian.net/rest/api/3/search/jql", params=params, headers=headers)

    if response.status_code != 200:
        return json.dumps(Response(True, "Issues could not be loaded."))
    
    results = []
    response = response.json()
    issues = response.get("issues", [])
    for issue in issues:
        key = issue["key"]
        summary = issue["fields"]["summary"]

        description_obj = issue["fields"].get("description")
        description_text = ""
        if description_obj and "content" in description_obj:
            # Extract plain text from nested description
            description_text = " ".join(
                node["text"]
                for block in description_obj["content"]
                for node in block.get("content", [])
                if node["type"] == "text"
            )
        results.append({"key": key, "summary": summary, "description": description_text})

    return json.dumps(results)

if __name__ == "__main__":
    mcp.run(transport="sse")
