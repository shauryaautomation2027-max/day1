from groq import Groq
from dotenv import load_dotenv
import json
import os

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

MODEL_NAME = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

SYSTEM_PROMPT = """
You are a workflow generation engine.

Convert user commands into workflow JSON.

Allowed components:
- gmail.read_email
- llm.summarize
- excel.compare_files
- sap.enter_data

Workflow format:
[
  {
    "step": 1,
    "component": "component_name",
    "params": {}
  }
]

Rules:
- Return ONLY valid JSON
- No explanation
- Use proper step ordering
"""

def validate_workflow(workflow):
    required_keys = {"step", "component", "params"}

    if not isinstance(workflow, list):
        return False

    for item in workflow:
        if not isinstance(item, dict):
            return False
        if not required_keys.issubset(item.keys()):
            return False

    return True

def generate_workflow(command: str):

    response = client.chat.completions.create(
        model=MODEL_NAME,
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": command
            }
        ]
    )

    content = response.choices[0].message.content

    try:
        workflow = json.loads(content)
        if validate_workflow(workflow):
            return workflow
        else:
            return {"error": "Schema validation failed"}

    except Exception as e:
        return {
            "error": "Invalid JSON returned",
            "raw_output": content
        }


if __name__ == "__main__":
    command = input("Enter command: ")
    result = generate_workflow(command)
    print(json.dumps(result, indent=2))
