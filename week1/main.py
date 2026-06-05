'''
yapay zeka ile konusmayi nasil yapacagiz?
- tenserflow (daha cok derin ogrenme ile ilgii)
- Langchain (LLM/yapay zekâ uygulamaları geliştirmeyi kolaylaştıran bir framework’tür.)(bunu sectik nedenleri derste anlatildi)
- Her llm'in kendi kütüphanesi (kendi SDK'leri)
    - OpenAI
    - Gemini
    - Anthropic
    - Grok
    - DeepSeek

- OpenRouter (OpenRouter, birçok farklı yapay zekâ modeline tek bir API üzerinden erişmeni sağlayan bir aracı platformdur.)

- LlamaIndex
- requests kütüphanesi ile http metodları aracılığla yz ile konusmak; fakat burada her seyi kendimiz sifirdan yapmak zorunda kaliriz.
- 
'''

from dotenv import load_dotenv
from langchain.agents import create_agent
import os

load_dotenv()

openrouterkey = os.getenv('OPENROUTER_API_KEY')

print(openrouterkey[-5:])

def get_weather(city: str) -> str:
    """Get weather for a given city."""
    return f"It's always sunny in {city}!"

agent = create_agent(
    model="openrouter:anthropic/claude-3.5-haiku",
    tools=[get_weather],
    system_prompt="You are a helpful assistant",
)

result = agent.invoke(
    {"messages": [{"role": "user", "content": "Who is the champion of the Türkiye's superlig football cup in 2026?"}]}
)

print(result)