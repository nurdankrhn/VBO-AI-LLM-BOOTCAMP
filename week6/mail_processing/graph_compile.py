from email_state import * # Local module
from read_and_classify_nodes import read_email, classify_intent # Local modeule
from search_and_tracking_nodes import search_documentation, bug_tracking # Local module
from response_nodes import draft_response, human_review, send_reply # Local module
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

# Create the graph
workflow = StateGraph(EmailAgentState)

# Add nodes with appropriate error handling
workflow.add_node("read_email", read_email)
workflow.add_node("classify_intent", classify_intent)
# Add retry policy for nodes that might have transient failures
workflow.add_node( "search_documentation", search_documentation)
workflow.add_node("bug_tracking", bug_tracking)
workflow.add_node("draft_response", draft_response)
workflow.add_node("human_review", human_review)
workflow.add_node("send_reply", send_reply)

# Edges
# Add only the essential edges
workflow.add_edge(START, "read_email")
workflow.add_edge("read_email", "classify_intent")
workflow.add_edge("send_reply", END)

# Compile with checkpointer for persistence, in case run graph with Local_Server --> Please compile without checkpointer
memory = MemorySaver()

app = workflow.compile(checkpointer=memory)

# Show workflow
# app_email = app.get_graph().draw_mermaid_png()
# with open("app_email.png", "wb") as f:
#     f.write(app_email)
# print("Graph saved as app_email.png")