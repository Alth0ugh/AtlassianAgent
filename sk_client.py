from argparse import ArgumentParser
import asyncio

import semantic_kernel as sk
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.ollama import OllamaChatCompletion, OllamaChatPromptExecutionSettings
from semantic_kernel.connectors.mcp import MCPSsePlugin
from semantic_kernel.contents.chat_history import ChatHistory

from servers.server_functions import convert_credentials

parser = ArgumentParser()
parser.add_argument("--ollama-address", type=str, help="Address and port for Ollama server.", required=True)
parser.add_argument("--mcp-address", type=str, help="Address and port of MCP server.", required=True)
parser.add_argument("--mail", type=str, help="User email", required=True)
parser.add_argument("--token", type=str, help="Atlassian ID token", required=True)

async def main(args):
    kernel = sk.Kernel()

    chat_service = OllamaChatCompletion("ollama", host=args.ollama_address, ai_model_id="mistral")

    kernel.add_service(chat_service)
    async with MCPSsePlugin("JiraPlugin", 
                            args.mcp_address, 
                            headers={
                                "Authorization": f"Basic {convert_credentials(args.mail, args.token)}"
                                }) as mcp_plugin:
        kernel.add_plugin(mcp_plugin)

        execution_settings = OllamaChatPromptExecutionSettings()
        execution_settings.function_choice_behavior = FunctionChoiceBehavior.Auto()

        chat = ChatHistory()
        chat.add_system_message("You are a helpful AI assistant that helps people with their requests. You can also call a plugin for manipulating with Jira tickets. For calling these plugins, you do not need login information. If the user does not supply you with all the arguments, ask for this information before using the plugin. If the operation fails, print the error message from the response.")

        service = kernel.get_service("ollama")

        while True:
            print("Prompt:")
            chat.add_user_message(input())

            completion = service.get_streaming_chat_message_contents(chat, execution_settings, kernel=kernel)

            full_message = ""
            print("Assistant:")
            async for content in completion:
                print(content[0].content, end="")
                full_message += content[0].content

            chat.add_assistant_message(full_message)
            print()
            print()


if __name__ == "__main__":
    args = parser.parse_args()
    asyncio.run(main(args))
