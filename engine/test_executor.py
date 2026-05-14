try:
    from engine.executor import execute_workflow
except ModuleNotFoundError:
    from executor import execute_workflow
import json

workflow = [
    {
        "step": 1,
        "component": "email_reader",
        "params": {}
    },
    {
        "step": 2,
        "component": "validator",
        "params": {}
    }
]

logs = execute_workflow(workflow)

print(json.dumps(logs, indent=2))
