from mcp.server.fastmcp import FastMCP

# 初始化FastMCP服务器
mcp = FastMCP("Calculator")

# 构建MCP工具
@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b

@mcp.tool()
def minus(a: int, b: int) -> int:
    """Subtract two numbers"""
    return a - b

@mcp.tool()
def multi(a: int, b: int) -> int:
    """Multiply two numbers"""
    return a * b

@mcp.tool()
def div(a: int, b: int) -> float:
    """Divide two numbers"""
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b

if __name__ == "__main__":
    # 使用标准输入输出流传输
    mcp.run(transport="stdio")
