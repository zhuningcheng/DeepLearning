from dotenv import load_dotenv
from openai import OpenAI  # 使用 OpenAI 客户端
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client
from typing import List, Dict, TypedDict
from contextlib import AsyncExitStack
import json
import asyncio
import os

load_dotenv()

class ToolDefinition(TypedDict):
    name: str
    description: str
    input_schema: dict

class MCP_ChatBot:

    def __init__(self):
        # Initialize session and client objects
        self.sessions: List[ClientSession] = []
        self.exit_stack = AsyncExitStack()
        
        # 设置 DeepSeek API 密钥
        api_key = "sk-0e90c3db27dd481f8542e1faf5cbf39e"
        # 创建 OpenAI 客户端，指向 DeepSeek API
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com/v1"
        )
        
        self.available_tools: List[ToolDefinition] = []
        self.tool_to_session: Dict[str, ClientSession] = {}

    async def connect_to_server(self, server_name: str, server_config: dict) -> None:
        """Connect to a single MCP server."""
        try:
            server_params = StdioServerParameters(**server_config)
            stdio_transport = await self.exit_stack.enter_async_context(
                stdio_client(server_params)
            )
            read, write = stdio_transport
            session = await self.exit_stack.enter_async_context(
                ClientSession(read, write)
            )
            await session.initialize()
            self.sessions.append(session)
            
            # List available tools for this session
            response = await session.list_tools()
            tools = response.tools
            print(f"\nConnected to {server_name} with tools:", [t.name for t in tools])
            
            for tool in tools:
                self.tool_to_session[tool.name] = session
                self.available_tools.append({
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.inputSchema
                })
        except Exception as e:
            print(f"Failed to connect to {server_name}: {e}")

    async def connect_to_servers(self):
        """Connect to all configured MCP servers."""
        try:
            with open("server_config.json", "r") as file:
                data = json.load(file)
            
            servers = data.get("mcpServers", {})
            
            for server_name, server_config in servers.items():
                await self.connect_to_server(server_name, server_config)
        except Exception as e:
            print(f"Error loading server configuration: {e}")
            raise
    
    async def process_query(self, query):
        try:
            messages = [{'role': 'user', 'content': query}]
            
            # 准备工具格式给 DeepSeek
            tools_for_deepseek = []
            for tool in self.available_tools:
                tools_for_deepseek.append({
                    "type": "function",
                    "function": {
                        "name": tool["name"],
                        "description": tool["description"],
                        "parameters": tool["input_schema"]
                    }
                })
            
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=messages,
                max_tokens=2024,
                tools=tools_for_deepseek,
                tool_choice="auto"
            )
            
            process_query = True
            while process_query:
                message = response.choices[0].message
                
                # 打印文本内容
                if message.content:
                    print(message.content)
                
                # 检查是否有工具调用
                if message.tool_calls:
                    for tool_call in message.tool_calls:
                        tool_name = tool_call.function.name
                        import json
                        tool_args = json.loads(tool_call.function.arguments)
                        
                        print(f"Calling tool {tool_name} with args {tool_args}")
                        
                        # 调用工具
                        session = self.tool_to_session[tool_name]
                        result = await session.call_tool(tool_name, arguments=tool_args)
                        
                        # 添加工具调用和结果到消息历史
                        messages.append({
                            "role": "assistant",
                            "content": None,
                            "tool_calls": [tool_call]
                        })
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": str(result.content)
                        })
                        
                        # 获取新的响应
                        response = self.client.chat.completions.create(
                            model="deepseek-chat",
                            messages=messages,
                            max_tokens=2024,
                            tools=tools_for_deepseek
                        )
                else:
                    process_query = False
                    
        except Exception as e:
            print(f"处理查询时出错: {e}")
            # 降级处理：不使用工具
            try:
                response = self.client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[{'role': 'user', 'content': query}],
                    max_tokens=2024
                )
                print(response.choices[0].message.content)
            except Exception as fallback_error:
                print(f"降级处理也失败: {fallback_error}")

    
    async def chat_loop(self):
        """Run an interactive chat loop"""
        print("\nMCP Chatbot Started!")
        print("Type your queries or 'quit' to exit.")
        
        while True:
            try:
                query = input("\nQuery: ").strip()
        
                if query.lower() == 'quit':
                    break
                    
                await self.process_query(query)
                print("\n")
                    
            except Exception as e:
                print(f"\nError: {str(e)}")
    
    async def cleanup(self):
        """Cleanly close all resources using AsyncExitStack."""
        await self.exit_stack.aclose()


async def main():
    chatbot = MCP_ChatBot()
    try:
        await chatbot.connect_to_servers()
        await chatbot.chat_loop()
    finally:
        await chatbot.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
