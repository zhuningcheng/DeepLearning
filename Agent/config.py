import openai
from openai import AsyncOpenAI
from agents.models import openai_provider
from agents import (
set_default_openai_api,
set_default_openai_client,
set_tracing_disabled
)
import os

# 对模型进行配置文件的设置，之后可以直接使用

api_key = os.environ["DEEPSEEK_API_KEY"]
url = os.environ["DEEPSEEK_API_BASE_URL"]

client = AsyncOpenAI(api_key= api_key,base_url = url)

# 使用自定义客户端
set_default_openai_client(client = client, use_for_tracing = False)

# 使用兼容的API模式
set_default_openai_api("chat_completions")

# 禁用OpenAI跟踪服务
set_tracing_disabled(disabled = True)

model_name = 'deepseek-chat'

openai_provider.DEFAULT_MODEL = model_name # 自定义模型名称
