# engine/executor.py

import json

try:
    from engine.component import (
        email_reader,
        pdf_parser,
        llm_extractor,
        validator,
    )
except ModuleNotFoundError:
    from component import (
        email_reader,
        pdf_parser,
        llm_extractor,
        validator,
    )

# component registry
COMPONENTS = {
    "email_reader": email_reader,
    "pdf_parser": pdf_parser,
    "llm_extractor": llm_extractor,
    "validator": validator,
    # Optional aliases for generated workflow names
    "gmail.read_email": email_reader,
    "llm.summarize": llm_extractor,
}


def execute_workflow(workflow):

    execution_log = []

    for step_data in workflow:

        step = step_data["step"]
        component_name = step_data["component"]
        params = step_data["params"]

        log_entry = {
            "step": step,
            "component": component_name
        }

        try:

            if component_name not in COMPONENTS:
                raise Exception(
                    f"Unknown component: {component_name}"
                )

            component_function = COMPONENTS[component_name]

            result = component_function(params)

            log_entry["status"] = "success"
            log_entry["result"] = result

        except Exception as e:

            log_entry["status"] = "failed"
            log_entry["error"] = str(e)

        execution_log.append(log_entry)

    return execution_log


if __name__ == "__main__":

    sample_workflow = [
        {
            "step": 1,
            "component": "email_reader",
            "params": {
                "folder": "inbox"
            }
        },
        {
            "step": 2,
            "component": "pdf_parser",
            "params": {
                "file": "invoice.pdf"
            }
        },
        {
            "step": 3,
            "component": "llm_extractor",
            "params": {}
        },
        {
            "step": 4,
            "component": "validator",
            "params": {}
        }
    ]

    logs = execute_workflow(sample_workflow)

    print(json.dumps(logs, indent=2))
