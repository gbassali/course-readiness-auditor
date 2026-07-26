import os
from deepagents import create_deep_agent
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

def calculate_total(weights: list[float]) -> float:
    """Calculates the total sum of a list of numerical weights."""
    print(f"Calculating total for weights: {weights}")
    return sum(weights)

policy_subagent = {
    "name": "policy_subagent",
    "description": "This subagent reviews policy statements and determines if they are clear or unclear.",
    "model": "google_genai:gemini-3.5-flash",
    "system_prompt": "Review a short policy statement and identify whether it is unclear."
}

instructions = "You are a course-readiness assistant. Respond clearly and briefly."
agent = create_deep_agent(
    model="google_genai:gemini-3.5-flash",
    tools = [calculate_total],
    system_prompt=instructions,
    subagents=[policy_subagent]
)

# results = agent.invoke({"messages": [{"role": "user", "content": "Calculate the total weight of the following assessments: 20, 30, 50."}]})
results = agent.invoke({"messages": [{"role": "user", "content": "Ask the policy reviewer whether this policy is clear: 'Late assignments may receive a penalty depending on the circumstances.'"}]})
# print(results["messages"][-1].content[0]["text"])
for message in results["messages"]:
    print(type(message).__name__)
    print(message.content)
    print()