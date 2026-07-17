from langgraph.graph import StateGraph, MessagesState, START, END
from typing import TypedDict


class NurdansCustomState(MessagesState):
    a: int
    b: str


def mock_llm(state: NurdansCustomState):
    return {"messages": [{"role": "ai", "content": "Ne yazarsan yaz karşında beni bulursun"}]}


graph = StateGraph(NurdansCustomState)


# İlk node
graph.add_node(mock_llm)

# Bağlantılar edges
graph.add_edge(START, "mock_llm")
graph.add_edge("mock_llm", END)

# Ağı copile et
graph = graph.compile()


# Ağı kullan
result = graph.invoke({"messages": [{"role": "user", "content": "Gel yanıma gel gel gel"}]})

print(result)
