from datetime import datetime

import chainlit as cl
from agents import Agent, Runner, function_tool


@function_tool
def get_weather(location: str) -> str:
    """Get the current weather for a location."""
    return f"Weather in {location}: 22°C, partly cloudy with light winds."


@function_tool
def get_weather_forecast(location: str, days: int = 3) -> str:
    """Get a multi-day weather forecast for a location."""
    lines = [
        f"Day {i + 1}: {21 + i}°C, {'sunny' if i % 2 == 0 else 'cloudy'}"
        for i in range(days)
    ]
    return f"{days}-day forecast for {location}:\n" + "\n".join(lines)


@function_tool
def get_current_time() -> str:
    """Get the current date and time."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@function_tool
def calculate(expression: str) -> str:
    """Evaluate a mathematical expression."""
    import math

    safe_globals = {k: v for k, v in vars(math).items() if not k.startswith("_")}
    try:
        result = eval(expression, {"__builtins__": {}}, safe_globals)
        return str(result)
    except Exception as exc:
        return f"Error evaluating expression: {exc}"


weather_agent = Agent(
    name="Weather Agent",
    model="gpt-4o",
    handoff_description="Specialist for weather conditions and forecasts.",
    instructions=(
        "You are a weather specialist. Use your tools to answer weather and forecast "
        "questions. Always state the location clearly in your response."
    ),
    tools=[get_weather, get_weather_forecast],
)

generic_agent = Agent(
    name="Generic Agent",
    model="gpt-4o",
    handoff_description="Handles general questions, time lookups, and math calculations.",
    instructions=(
        "You are a helpful general assistant. You can look up the current time and "
        "evaluate mathematical expressions. Be concise and direct."
    ),
    tools=[get_current_time, calculate],
)

router_agent = Agent(
    name="Router Agent",
    model="gpt-4o",
    instructions=(
        "You are a routing agent. Hand off every request to the right specialist:\n"
        "- Weather Agent: weather conditions, forecasts, or any climate question\n"
        "- Generic Agent: time, math, and all other topics\n"
        "Never answer directly. Always hand off."
    ),
    handoffs=[weather_agent, generic_agent],
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

    result = await Runner.run(router_agent, history)
    reply = result.final_output

    msg.content = reply
    await msg.update()

    cl.user_session.set("history", result.to_input_list())
