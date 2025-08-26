import semantic_kernel as sk
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.ollama import OllamaChatCompletion
import asyncio
from semantic_kernel.connectors.ai.ollama import OllamaChatPromptExecutionSettings
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.functions import kernel_function
from semantic_kernel.connectors.ai.open_ai import OpenAIPromptExecutionSettings
from semantic_kernel.connectors.mcp import MCPSsePlugin


class FilePlugin:
    @kernel_function(description="Saves text into a file. The first argument is file_name which is a string containing the name of the file. The second argument is content, which is the content of the file. Returns True if the action was executed sucessfully.")
    def save_to_file(file_name, content):
        with open(file_name, "w") as f:
            f.write(content)
        return True

async def main():
    # Step 1: Initialize the kernel
    kernel = sk.Kernel()

    chat_service = OllamaChatCompletion("ollama", host="http://localhost:11434", ai_model_id="MFDoom/deepseek-r1-tool-calling:8b")

    # Step 3: Register the service with the kernel
    kernel.add_service(chat_service)
    # kernel.add_plugin(FilePlugin, "FilePlugin")
    async with MCPSsePlugin("JiraPlugin", "http://localhost:8000/sse") as mcp_plugin:
        kernel.add_plugin(mcp_plugin)
        # await mcp_plugin.call_tool("register_credential", email="oliver.piter", token="token")
        execution_settings = OllamaChatPromptExecutionSettings()
        execution_settings.function_choice_behavior = FunctionChoiceBehavior.Auto()
        chat = ChatHistory()
        service = kernel.get_service("ollama")
        chat.add_system_message("You are a helpful AI assistant that helps people with their requests. You can also call a plugin for manipulating with Jira tickets. For calling these plugins, you do not need login information. If the user does not supply you with all the arguments, ask for this information before using the plugin. If the operation fails, print the error message from the response.")

        while True:
            print("Prompt:")
            chat.add_user_message(input())

            completion = service.get_streaming_chat_message_contents(chat, execution_settings, kernel=kernel)

            full_message = ""
            async for content in completion:
                print(content[0].content, end="")
                full_message += content[0].content

            

            chat.add_assistant_message(full_message)
            print()


if __name__ == "__main__":
    asyncio.run(main())
