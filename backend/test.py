
from pydantic_ai import Agent

agent = Agent(
    "gpt-4o-mini",
    instructions="Reply with one word."
)

result = agent.run_sync("Say hello")
print(result.output)
