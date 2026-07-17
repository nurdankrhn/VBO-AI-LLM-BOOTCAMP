from typing import Literal
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langchain.chat_models import init_chat_model
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import os

load_dotenv()

model = init_chat_model(
        "openai:google/gemini-2.5-flash-lite",
        api_key=os.getenv("OPENROUTER_API_KEY"),
        base_url="https://openrouter.ai/api/v1",
        max_tokens=500)

class IsJokeCool(BaseModel):
    decision: Literal["Pass", "Fail"] = Field(
        description="'Pass' if the joke is cool, 'Fail' if it is terrible/bad/cliché."
    )

# Graph state
class State(TypedDict):
    topic: str
    joke: str
    improved_joke: str
    final_joke: str

# Node functions
def generate_joke(state: State):
    """Node: First LLM call to generate initial joke"""
    print("Executing node: generate_joke")

     # Uncomment for successful case (joke passes punchline check):
    msg = model.invoke(f"Write a short joke about {state['topic']}")
    joke = msg.content
    
    # Force a joke without punctuation to trigger the fail scenario
    # joke = "Cats are very lazy animals that sleep all day"
    # print(f"Generated joke: {joke}")
    return {"joke": joke}

def improve_joke(state: State):
    """Node: Second LLM call to improve the joke"""
    print("Executing node: improve_joke")

    msg = model.invoke(f"Make this joke funnier by adding wordplay: {state['joke']}")
    print(f"Improved joke: {msg.content}")
    return {"improved_joke": msg.content}

def polish_joke(state: State):
    """Node: Third LLM call for final polish"""
    print("Executing node: polish_joke")

    msg = model.invoke(f"Add a surprising twist to this joke: {state['improved_joke']}")
    print(f"Final joke: {msg.content}")
    return {"final_joke": msg.content}


# Edges
# Conditional edge function
def decide_joke_is_cool(state: State):
    """Conditional edge: Gate function to check if the joke has a punchline"""
    print("Checking joke is cool...")

    # # Simple check - does the joke contain "?" or "!"
    # if "?" in state["joke"] or "!" in state["joke"]:
    #     print("Punchline check: PASS - Going to END")
    #     return "Pass"
    # print("Punchline check: FAIL - Going to improve_joke")
    # return "Fail"

    structured_model = model.with_structured_output(IsJokeCool)
    llm_cool_joke_decision = structured_model.invoke(f"Evaluate this joke: {state['joke']} and decide if it is cool or terrible, bad, cliche then return Pass if cool else Fail")

    print("llm_cool_joke_decision", llm_cool_joke_decision)

    # Return the string key ("Pass"/"Fail") that the conditional-edge map expects,
    # NOT the whole IsJokeCool object (which is unhashable and can't be a route key).
    return llm_cool_joke_decision.decision



# Build workflow
workflow = StateGraph(State)

workflow.add_node("generate_joke", generate_joke)
workflow.add_node("improve_joke", improve_joke)
workflow.add_node("polish_joke", polish_joke)

# Add edges to connect nodes
workflow.add_edge(START, "generate_joke")
workflow.add_edge("improve_joke", "polish_joke")
workflow.add_edge("polish_joke", END)

# Add conditional edge
workflow.add_conditional_edges(
    "generate_joke", decide_joke_is_cool, {"Fail": "improve_joke", "Pass": END}
)

graph = workflow.compile()


# Show workflow
graph_png = graph.get_graph().draw_mermaid_png()
with open("workflow_graph.png", "wb") as f:
    f.write(graph_png)
print("Graph saved as workflow_graph.png")

joke_final_result = graph.invoke({"topic": "cats"})

print(joke_final_result)