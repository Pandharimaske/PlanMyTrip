"""
Conversational replanning agent.
Lets users modify itinerary via natural language:
  - "Replace Day 2 evening with something near the beach"
  - "I have only ₹8000 budget now, adjust"
  - "Add more food spots on Day 1"
  - "What time does Taj Mahal open?"
"""

import os, json
from langchain_groq import ChatGroq

llm = ChatGroq(
    api_key=os.getenv("GROQ_API_KEY"),
    model="llama3-70b-8192",
    temperature=0.6,
    max_tokens=4096,
)

SYSTEM_PROMPT = """You are PlanMyTrip's AI travel assistant. You have access to the user's current itinerary.

You can:
1. MODIFY the itinerary based on user requests (change places, adjust budget, swap days, add/remove activities)
2. ANSWER questions about the trip (costs, timings, distances, what to expect)
3. SUGGEST alternatives when asked

Response rules:
- If the user wants a modification, return JSON with:
  {"type": "update", "itinerary": <full updated itinerary JSON>, "message": "short explanation of changes"}
- If the user is asking a question (no modification needed), return JSON with:
  {"type": "answer", "message": "your answer here"}
- ALWAYS return valid JSON only, no extra text
- Keep the same JSON structure as the original itinerary
- Be conversational and helpful in the message field
"""

async def handle_chat(message: str, itinerary: dict, history: list) -> dict:
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    for turn in history[-6:]:
        messages.append({"role": turn["role"], "content": turn["content"]})

    user_content = f"""Current itinerary:
{json.dumps(itinerary, indent=2)}

User request: {message}"""

    messages.append({"role": "user", "content": user_content})

    response = llm.invoke(messages)
    content = response.content.strip()

    start = content.find("{")
    end = content.rfind("}") + 1
    if start != -1 and end > 0:
        try:
            return json.loads(content[start:end])
        except json.JSONDecodeError:
            pass

    return {
        "type": "answer",
        "message": content or "I couldn't process that. Please try again."
    }
