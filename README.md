# Aim of the project

This project demonstrates how to connect LLM-powered [agents](https://www.anthropic.com/engineering/building-effective-agents) with [Jira]((https://developer.atlassian.com/cloud/jira/platform/rest/v3/intro/)) and [Confluence](https://developer.atlassian.com/cloud/confluence/rest/v2/intro/#about) using the [Model Context Protocol](https://modelcontextprotocol.io/docs/getting-started/intro). By combining reasoning and automation from large language models with Jira/Confluence APIs, the system can:

* Automate and simplify common Jira workflows (e.g., creating, updating, and querying issues).

* Provide intelligent interaction with Confluence content, including retrieving pages, generating summaries, and assisting with documentation tasks.

* Allow users to control these platforms using natural language.

# Scope
## Servers
[jira_server_stdio.py](servers/jira_server_stdio.py) implements tools for:
* ticket creation
* assigning user to a ticket
* updating ticket status
* loading tickets related to a specific project

[confluence_server_stdio.py](servers/confluence_server_stdio.py) features:
* page creation
* searching for a specific page

LLM agents can connect to these servers with STDIO method.

One additional server [jira_server.py](servers/jira_server.py) has been implemented. This server contains only tools for ticket creation and listing of tickets. Agents can connect to this server using the SSE method.

## Agents
One custom agent [sk_client.py](clients/sk_client.py) was implemented using [Semantic Kernel](https://github.com/microsoft/semantic-kernel) and [Ollama](https://ollama.com/) for easy LLM integration. For testing purposes, [Mistral 7B Instruct](https://ollama.com/library/mistral:7b-instruct) was selected. This agent is used for connecting to [jira_server.py](servers/jira_server.py) server.

The other agent used for testing the [MCP](https://modelcontextprotocol.io/docs/getting-started/intro) servers was [Claude Desktop](https://claude.ai/download).

# Conclusions
Implementing [MCP](https://modelcontextprotocol.io/docs/getting-started/intro) is an easy way to add more capabilities to LLMs beyond chatting. The two agents described in the section above were compared in terms of the ability to call tools from the [MCP](https://modelcontextprotocol.io/docs/getting-started/intro) server, orchestration ability, hallucinations, and interaction with human.

## Tool calling
The [Mistral 7B Instruct](https://ollama.com/library/mistral:7b-instruct) agent showed the ability to call very simple server with one simple tool for ticket creation. Once more tools were introduced, the model failed to generate proper tool call response defined by [Semantic Kernel](https://github.com/microsoft/semantic-kernel) completely failing to execute any tool. The response usually contained the correct function signature, showing that the model was aware about the function and its parameters, but usually generated a JavaScript code for the user to run the code by themselves. Giving more specific instructions to the model generally did not help and the model almost always failed to generate proper tool calling.

[Claude Desktop](https://claude.ai/download) agent showed good tool calling and understanding ability for the tools. The agent knew when to execute a tool regardless of whether it was explicitely instructed to do so by the user or not.

## Orchestration
As [Mistral 7B Instruct](https://ollama.com/library/mistral:7b-instruct) failed to call tools from the server, it does not feature any form of orchestration ability.

[Claude Desktop](https://claude.ai/download) showed a good level of orchestration ability in various ways. It could generate multiple function calls on one server (check available transitions for a ticket, trasition a ticket using available transitions) without explicit instructions from the user, and also cross-server orchestration (read the description of a Jira ticket and create new Confluence page containing the description from the ticket).

## Hallucinations
[Mistral 7B Instruct](https://ollama.com/library/mistral:7b-instruct) agent in the cases when the agent successfully invoked a tool showed signs of hallucinations on multiple occasions, usually when supplying parameters into the function. For example, when there was no assignee specified for a new ticket, the model supplied "no user" to the parameter, instead of leaving the parameter empty.

[Claude Desktop](https://claude.ai/download) did not show any signs of hallucinations and always kept the parameters as they were, including grammatical mistakes, upper/lowers case, nonsensical words, etc.

## Interaction with the human
[Mistral 7B Instruct](https://ollama.com/library/mistral:7b-instruct) showed some level of understanding of the tools and when some information was missing from the user, the model asked the user for it. In many cases, when the user supplied additional information, the model forgot about it and asked about it again, or even responded with the user-supplied information and asked to user to repeat it again. Additionally, the agent would ask the user for additional information by providing an example of the code the agent needs to run, making it very poor user experience.

[Claude Desktop](https://claude.ai/download) could ask for additional information in a very clear way and once it was supplied with sufficient parameters, a tool call was executed. If a tool failed, the model told the user what error occured and asked the user to clarify their needs and confirm the information given.

## Overall
In conclusion, [Claude Desktop](https://claude.ai/download) showed better abilities to become a personal assistant utilizing tools to interact with external systems. [Mistral 7B Instruct](https://ollama.com/library/mistral:7b-instruct) failed to demonstrate abilities to become such assistant, most likely due to a very small number of parameters (7B) making the model good for language modelling and chatting but not for agentic use cases. Other LLM variants such as Deepseek models were tested but all failed due to the lack of tool calling support in [Ollama](https://ollama.com/).

# How to run
In order to run the agents, install [Ollama](https://ollama.com/) on your system and install a model of your choosing if you want to run agents from [Ollama](https://ollama.com/), otherwise install [Claude Desktop](https://claude.ai/download). Then, install [requirements.txt](requirements.txt) in your Python environment.

## Generate Atlassian ID access token
Visit [https://support.atlassian.com/atlassian-account/docs/manage-api-tokens-for-your-atlassian-account/](https://support.atlassian.com/atlassian-account/docs/manage-api-tokens-for-your-atlassian-account/) and generate access tokens using manual in section **Create an API token**. Save your token for future use.

## Running Ollama agents
Run [jira_server.py](servers/jira_server.py) in the following way:

    python servers/jira_server.py --space {name_of_jira_space} --host {host_ip_address} --port {host_port}
then, run [sk_client.py](clients/sk_client.py) the following way
    
    python clients/sk_client.py --ollama-address {ollama_address:ollama_port} --mcp-address {mcp_address:mcp_port}/sse --mail {user@email.com} --token {atlassian_id_token} --model-id {ollama_model_id}

The agent should connect to the server using SSE and a chat with the model opens.

## Running Claude Desktop
Open Claude Desktop. Go to Settings > Developer > Edit config. Replace the config with the following:

    {
    "mcpServers": {
        "jira": {
        "command": "python",
        "args": [
            "{path_to_repository}/jira_server_stdio.py",
            "--space",
            "{space}",
            "--mail",
            "{mail}",
            "--token",
            "{atlassian_id_token}"
        ]
        },
        "confluence": {
        "command": "python",
        "args": [
            "{path_to_repository}/confluence_server.py",
            "--space",
            "{space}",
            "--mail",
            "{mail}",
            "--token",
            "{atlassian_id_token}"
        ]
        }
    }
    }


Modify the parameters in curly braces according to you paths and login information. Then, restart the application. After start, [Claude Desktop](https://claude.ai/download) starts the servers on the background.

## Sample prompts
* Create new Jira ticket for me.
* Create new Confluence page for me.
* Create Jira ticket with summary: " ... ", description: " ... ", project: " ... " and assign it to user with email " ... ".
* List me all tickets from project " ... " where user " ... " is assigned.
* Find me issue with key " ... " in project " ... " and copy this issue with summary " (new summary) "
* Find me issue with key " ... " in project " ... " and create new Confluence page containing the description of the issue in the content and issue key in the title.
