# DeepSeek Multimodal Chatbot

This project shows how to build a Python chatbot that can reason over both text and images using the DeepSeek LLM API. It ships with a simple CLI example plus helper classes for managing prompts, multimodal payloads, and conversation state.

## 1. Prerequisites

- Python 3.10+
- A DeepSeek API key with access to the `deepseek-chat` (multimodal) model
- `pip install -r requirements.txt` *(see below)*

## 2. Setup

1. Create a virtual environment and install dependencies:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. Export your DeepSeek credentials:

   ```bash
   export DEEPSEEK_API_KEY="Your_API_KEYS"
   # Optional overrides:
   # export DEEPSEEK_BASE_URL="https://api.deepseek.com"
   # export DEEPSEEK_CHAT_PATH="/chat/completions"
   ```

3. Run the sample CLI:

   ```bash
   python -m app.main "Summarize this sunset photo" --image ./examples/sunset.jpg --pretty
   ```

## 3. Project Structure

- `app/config.py` – loads and validates environment variables.
- `app/deepseek_client.py` – converts text + images into the JSON payload expected by DeepSeek and issues HTTP requests.
- `app/chatbot.py` – maintains conversation history and offers convenience methods for text-only or multimodal turns.
- `app/main.py` – minimal CLI wrapper so you can try the chatbot locally.

## 4. Multi-Agent Orchestration

To extend the chatbot with specialised multi-agent behaviour:

- **Planner Agent**: interprets the user’s high-level goal and decomposes it into steps. Uses the chatbot to gather missing info.
- **Specialist Agents**: each agent owns a type of task (e.g. `Vision Analyst`, `Researcher`, `Coder`) and receives sub-prompts from the planner. They call the chatbot with task-specific system prompts.
- **Controller / Orchestrator**: manages the workflow, decides which agent should act next, and aggregates their outputs into a final reply.

You can build this controller with frameworks like Haystack Agents, LangGraph, or a custom Python loop. A sketch using plain Python:

```python
from app.chatbot import DeepSeekChatbot

planner = DeepSeekChatbot(system_prompt="You plan and assign tasks to specialists.")
vision = DeepSeekChatbot(system_prompt="You describe and interpret images in detail.")
researcher = DeepSeekChatbot(system_prompt="You fetch and summarise background knowledge.")

def solve(task, images=None):
    plan, _ = planner.send_text(f"Task: {task}\nReturn numbered steps.")
    steps = plan.splitlines()
    results = []
    for step in steps:
        if "image" in step.lower():
            result, _ = vision.send_with_images(step, image_paths=images or [])
        else:
            result, _ = researcher.send_text(step)
        results.append(result)
    final_answer, _ = planner.send_text(
        f"Task: {task}\nSteps:\n{plan}\nResults:\n" + "\n".join(results)
    )
    return final_answer
```

Key ideas:

- **Shared context**: pass summaries between agents so they stay aligned without sharing the full token history.
- **Guard rails**: add system prompts that constrain each agent’s behaviour; enforce validation on their outputs.
- **Tool use**: agents can call external tools (search, code exec) before reporting back, letting you automate complex tasks.

## 5. Extending the Chatbot

- Build a REST API (e.g. FastAPI) that wraps `DeepSeekChatbot`.
- Add streaming responses by switching to the DeepSeek streaming endpoint.
- Persist conversation history in a database or vector store for long-term memory.
- Integrate voice and camera inputs to capture multimodal prompts dynamically.

## 6. Requirements File

Create `requirements.txt` with:

```
requests>=2.32.3
python-dotenv>=1.0.1
```

(`python-dotenv` is optional but handy if you prefer loading secrets from a `.env` file.)

## 7. Troubleshooting

- `MissingAPIKeyError`: ensure `DEEPSEEK_API_KEY` is exported in your shell or stored via `.env`.
- 401/403 errors: verify the key has permission for the model you selected.
- 415 or 422 errors: confirm images are readable files, and their MIME types are supported (`jpeg`, `png`, `webp`, etc.).

Happy building!


