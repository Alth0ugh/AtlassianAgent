from dataclasses import dataclass
from typing import Optional
import json

@dataclass(init=True)
class CreateRequest:
    project: str
    summary: str
    description: str
    assignee: str | None

    def to_json(self) -> str:
        data = { "fields": {
            "project": {
                "key": self.project
            },
            "summary": self.summary,
            "description": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {
                                "text": self.description,
                                "type": "text"
                            }
                        ]
                    }
                ]
            },
            "assignee": {},
            "issuetype": {
                "name": "Task"
            }
        } }
        if self.assignee is not None:
            data["fields"]["assignee"] = {"id": self.assignee}

        return json.dumps(data, indent=4)