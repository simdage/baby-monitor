from google.adk.agents.llm_agent import Agent
from src.api.db import log_manual_event_bigquery

root_agent = Agent(
    model='gemini-2.5-flash',
    name='root_agent',
    description='A helpful assistant for user questions.',
    instruction='Answer user questions to the best of your knowledge',
    tools=[log_manual_event_bigquery]
)
