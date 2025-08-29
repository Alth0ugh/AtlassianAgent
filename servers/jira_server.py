from argparse import ArgumentParser
from dataclasses import asdict
import json

from mcp.server.fastmcp import Context, FastMCP
import requests

from jira_create_request import CreateRequest
from server_functions import *
from server_response import Response

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
def create_ticket(ctx: Context, summary: str, description: str, project: str, assignee: str) -> str:
    """
    Creates Jira ticket.

    Parameters:
        ctx (Context): Injected parameter.
        summary (str): Ticket summary.
        description (str): Description of the ticket.
        project (str): Project where the ticket will be assigned.
        assignee (Optional[str]): Assignee's email.

    Returns:
        str: JSON encoded Response object.
    """
    credentials = get_credentials(ctx)
    if credentials is None:
        return json.dumps(Response(True, "No valid credentials were found in the request."))
    headers = get_headers(credentials)
    
    assignee_id = None

    if assignee is not None:
        parameters = {
            "query": f"{assignee}"
        }
        response = requests.get(f"https://{args.space}.atlassian.net/rest/api/3/user/search", headers=headers, params=parameters)

        if response.status_code == 200:
            response = response.json()
            assignee_id = response[0]["accountId"]
    
    request = CreateRequest(project, summary, description, assignee_id)
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
def load_tickets_for_project(ctx: Context, project_key: str) -> str:
    """
    Loads tickets assigned to the project.

    Parameters:
        ctx (Context): Injected parameter
        project_key (str): Key of the project.

    Returns:
        str: JSON array with tickets or in case of an error encoded Response object.
    """
    credentials = get_credentials(ctx)
    if credentials is None:
        return json.dumps(Response(True, "No valid credentials were found in the request."))
    headers = get_headers(credentials)
    params = {
        "jql": f'project = "{project_key}" ORDER BY created DESC',
              "fields": "summary, description,assignee,status"
    }

    response = requests.get(f"https://{args.space}.atlassian.net/rest/api/3/search/jql", params=params, headers=headers)

    if response.status_code != 200:
        return json.dumps(asdict(Response(True, "Issues could not be loaded.")))
    
    results = []
    response = response.json()
    issues = response.get("issues", [])
    for issue in issues:
        key = issue["key"]
        summary = issue["fields"]["summary"]
        status = issue["fields"]["status"]["name"]
        assignee = issue["fields"]["assignee"]
        assignee_name = ""
        assignee_email = ""

        if assignee is not None:
            assignee_name = issue["fields"]["assignee"].get("displayName", "")
            assignee_email = issue["fields"]["assignee"].get("emailAddress", "")

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
        results.append({"key": key, "summary": summary, "description": description_text, "status": status, "assignee_name": assignee_name, "assignee_mail": assignee_email})

    return json.dumps(results)

if __name__ == "__main__":
    mcp.run(transport="sse")
