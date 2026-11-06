from langgraph.types import Command
from app.workflow.flow import graph

# Each candidate has their own save slot
config = {"configurable": {"thread_id": "test-candidate-1"}}

print("--- Start ---")
graph.invoke({"candidate_id": 1}, config)
print("Waiting for HR:", graph.get_state(config).next)

print("--- HR stop 1: yes ---")
graph.invoke(Command(resume="yes"), config)
print("Waiting for HR:", graph.get_state(config).next)

print("--- HR stop 2: yes ---")
graph.invoke(Command(resume="yes"), config)
print("Waiting for HR:", graph.get_state(config).next)

print("--- HR stop 3: yes ---")
graph.invoke(Command(resume="yes"), config)
print("Finished:", graph.get_state(config).next)

# A second candidate, and HR says no
config_2 = {"configurable": {"thread_id": "test-candidate-2"}}

print("--- Second candidate ---")
graph.invoke({"candidate_id": 2}, config_2)

print("--- HR stop 1: no ---")
graph.invoke(Command(resume="no"), config_2)
print("Finished:", graph.get_state(config_2).next)
