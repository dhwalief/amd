from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    base_url="http://134.199.206.176:8000/v1",
    api_key="dummy",
    model="qwen2.5:3b",
    temperature=0.7,
)

response = llm.invoke("Halo")

print(response.content)