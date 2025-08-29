from argparse import ArgumentParser
from dataclasses import asdict
from typing import Optional
import json

from mcp.server.fastmcp import FastMCP
import requests

from jira_create_request import CreateRequest
from server_functions import *
from server_response import Response

parser = ArgumentParser()
parser.add_argument("--space", type=str, help="Name of the Atlassian space.", required=True)
parser.add_argument("--mail", type=str, help="User email.", required=True)
parser.add_argument("--token", type=str, help="User Atlassian ID token.", required=True)
args = parser.parse_args()

mcp = FastMCP(
    name="JiraServer"
)

def get_user_id(mail: str) -> Optional[str]:
    """
    Queries Jira API for user ID by user email.

    Parameters:
        mail (str): User email.

    Returns:
        Optional[str]: User ID or None if the ID is not found.
    """
    credentials = convert_credentials(args.mail, args.token)
    headers = get_headers(credentials)
    parameters = {
        "query": f"{mail}"
    }
    response = requests.get(f"https://{args.space}.atlassian.net/rest/api/3/user/search", headers=headers, params=parameters)

    if response.status_code == 200:
        response = response.json()
        assignee_id = response[0]["accountId"]
        return assignee_id
    return None

@mcp.tool(description="""Creates a ticket in Jira. 
          Parameters:
          summary: summary of the ticket
          description: description of the ticket
          project: project where ticket is assigned
          assignee: (Optional) assignee for the ticket. Provide user email.

          Returns:
          A response object with the following properties: is_error: boolean indicating whether an error occured, error_message: string containing error message if an error occured.""")
def create_ticket(summary: str, description: str, project: str, assignee: Optional[str]) -> str:
    """
    Creates Jira ticket.

    Parameters:
        summary (str): Ticket summary.
        description (str): Description of the ticket.
        project (str): Project where the ticket will be assigned.
        assignee (Optional[str]): Assignee's email.

    Returns:
        str: JSON encoded Response object.
    """
    credentials = convert_credentials(args.mail, args.token)
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
        return json.dumps(asdict(Response(False)))
    elif response.status_code == 400:
        return json.dumps(asdict(Response(True, "The request was malformed.")))
    elif response.status_code == 401:
        return json.dumps(asdict(Response(True, "User cannot be authenticated.")))
    elif response.status_code == 403:
        return json.dumps(asdict(Response(True, "User does not have permissions for this operaiton.")))
    elif response.status_code == 422:
        return json.dumps(asdict(Response(True, "Configuration problem prevents execution of this operation.")))
    return json.dumps(asdict(Response(True, "No valid credentials were found in the request.")))

@mcp.tool(description="""Assigns user to an issue.
          
          Parameters:
          mail: email of the user
          issue_key: the key of the issue
          
          Returns:
          A response object with the following properties: is_error: boolean indicating whether an error occured, error_message: string containing error message if an error occured.
          """)
def assign_user_to_issue(mail: str, issue_key: str) -> str:
    """
    Assigns user to an issue.

    Parameters:
          mail (str): Email of the user.
          issue_key (str): The key of the issue.

    Returns:
        str: JSON encoded Response object.
    """
    user_id = get_user_id(mail)
    credentials = convert_credentials(args.mail, args.token)
    headers = get_headers(credentials)
    body = {"accountId": user_id}

    response = requests.put(f"https://{args.space}.atlassian.net/rest/api/3/issue/{issue_key}/assignee", headers=headers, data=json.dumps(body))

    if response.status_code == 204:
        return json.dumps(asdict(Response(False)))
    elif response.status_code == 404:
        return json.dumps(asdict(Response(True, "The user or the issue does not exist")))
    
    return json.dumps(asdict(Response(True, "Unexpected error occured")))

@mcp.tool(description="""Gets all available status transitions for Jira issue.
          
          Parameters:
          issue_key: key of the issue
          
          Returns:
          A list of transition names and IDs.
          In case of error returns a response object with the following properties: is_error: boolean indicating whether an error occured, error_message: string containing error message if an error occured.
          """)
def get_available_transitions(issue_key: str) -> str:
    """
    Gets available transitions for an issue.

    Parameters:
        issue_key (str): Key of the issue.

    Returns:
        str: JSON containing available trasitions or serialized Response containing error.
    """
    credentials = convert_credentials(args.mail, args.token)
    headers = get_headers(credentials)

    response = requests.get(f"https://{args.space}.atlassian.net/rest/api/3/issue/{issue_key}/transitions", headers=headers)
    if response.status_code != 200:
        return json.dumps(asdict(Response(True, "Could not load available transitions")))
    
    response = response.json()

    transitions = response["transitions"]
    transitions_list = []
    for transition in transitions:
        transitions_list.append({"name": transition["name"], "id": transition["id"]})
    
    return json.dumps(transitions_list)

@mcp.tool(description="""Transitions Jira issue from one state to another.
          
          Parameters:
          issue_key: key of the issue
          transition_id: ID of the transition to be applied
          
          Returns:
          A response object with the following properties: is_error: boolean indicating whether an error occured, error_message: string containing error message if an error occured.
          """)
def transition_issue(issue_key: str, transition_id: str) -> str:
    """
    Updates the status of the issue.

    Parameters:
        issue_key (str): Key of the issue.
        transition_id (str): The ID of available transition.

    Returns:
        str: JSON encoded Response object.
    """
    credentials = convert_credentials(args.mail, args.token)
    headers = get_headers(credentials)
    body = {"transition": transition_id}

    response = requests.post(f"https://{args.space}.atlassian.net/rest/api/3/issue/{issue_key}/transitions", headers=headers, data=json.dumps(body))
    
    if response.status_code == 204:
        return json.dumps(asdict(Response(False)))
    elif response.status_code == 400:
        return json.dumps(asdict(Response(True, "This status does not exist.")))
    elif response.status_code == 404:
        return json.dumps(asdict(Response(True, "Issue does not exist.")))
    return json.dumps(asdict(Response(True, "Unexpected error occured.")))

@mcp.tool(description="""Lists all tickets assigned to the project. This tools does not need any parameters. 
          
          Returns:
          A list of issues with key, summary and description of each issue. 
          If error occurs, returns json with the following properties: is_error: boolean indicating whether an error occured, error_message: string containing error.""")
def load_tickets_for_project(project_key: str) -> str:
    """
    Loads tickets assigned to the project.

    Parameters:
        project_key (str): Key of the project.

    Returns:
        str: JSON array with tickets or in case of an error encoded Response object.
    """
    credentials = convert_credentials(args.mail, args.token)
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
            description_text = " ".join(
                node["text"]
                for block in description_obj["content"]
                for node in block.get("content", [])
                if node["type"] == "text"
            )
        results.append({"key": key, "summary": summary, "description": description_text, "status": status, "assignee_name": assignee_name, "assignee_mail": assignee_email})

    return json.dumps(results)

if __name__ == "__main__":
    mcp.run(transport="stdio")
