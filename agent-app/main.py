from datetime import datetime

import chainlit as cl
from deepagents import create_deep_agent
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4o")


def get_weather(location: str) -> str:
    """Get the current weather for a location."""
    return f"Weather in {location}: 22°C, partly cloudy with light winds."


def get_weather_forecast(location: str, days: int = 3) -> str:
    """Get a multi-day weather forecast for a location."""
    lines = [
        f"Day {i + 1}: {21 + i}°C, {'sunny' if i % 2 == 0 else 'cloudy'}"
        for i in range(days)
    ]
    return f"{days}-day forecast for {location}:\n" + "\n".join(lines)


def get_current_time() -> str:
    """Get the current date and time."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def calculate(expression: str) -> str:
    """Evaluate a mathematical expression."""
    import math

    safe_globals = {k: v for k, v in vars(math).items() if not k.startswith("_")}
    try:
        result = eval(expression, {"__builtins__": {}}, safe_globals)
        return str(result)
    except Exception as exc:
        return f"Error evaluating expression: {exc}"


weather_subagent = {
    "name": "weather-agent",
    "description": "Specialist for weather conditions and forecasts.",
    "system_prompt": (
        "You are a weather specialist. Use your tools to answer weather and forecast "
        "questions. Always state the location clearly in your response."
    ),
    "tools": [get_weather, get_weather_forecast],
}

generic_subagent = {
    "name": "generic-agent",
    "description": "Handles general questions, time lookups, and math calculations.",
    "system_prompt": (
        "You are a helpful general assistant. You can look up the current time and "
        "evaluate mathematical expressions. Be concise and direct."
    ),
    "tools": [get_current_time, calculate],
}

agent = create_deep_agent(
    model=llm,
    subagents=[weather_subagent, generic_subagent],
    system_prompt=(
        "You are a routing agent. Delegate every request to the right specialist:\n"
        "- weather-agent: weather conditions, forecasts, or any climate question\n"
        "- generic-agent: time, math, and all other topics\n"
        "Never answer directly. Always delegate to a subagent."
    ),
)


@cl.on_chat_start
async def on_chat_start():
    cl.user_session.set("history", [])


@cl.on_message
async def on_message(message: cl.Message):
    history = cl.user_session.get("history", [])
    history.append({"role": "user", "content": message.content})

    msg = cl.Message(content="")
    await msg.send()

    async for event in agent.astream_events({"messages": history}, version="v2"):
        if event["event"] == "on_chat_model_stream":
            chunk = event["data"]["chunk"]
            content = chunk.content
            if isinstance(content, str):
                await msg.stream_token(content)
            elif isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get("text"):
                        await msg.stream_token(block["text"])

    await msg.update()

    history.append({"role": "assistant", "content": msg.content})
    cl.user_session.set("history", history)
