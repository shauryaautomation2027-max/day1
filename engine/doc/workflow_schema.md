# Workflow JSON Schema

Each workflow is returned as a JSON array.

## Structure

```json
[
  {
    "step": 1,
    "component": "component_name",
    "params": {}
  }
]
```

## Fields

| Field | Type | Description |
|------|------|-------------|
| step | integer | Execution order |
| component | string | Action/component name |
| params | object | Parameters for component |

## Supported Components

| Component | Description |
|-----------|-------------|
| gmail.read_email | Read emails from Gmail |
| llm.summarize | Summarize content |
| excel.compare_files | Compare Excel files |
| sap.enter_data | Enter data into SAP |

## Example

```json
[
  {
    "step": 1,
    "component": "gmail.read_email",
    "params": {
      "filter": "unread"
    }
  }
]
```