from dataclasses import dataclass
import json

@dataclass(init=True)
class CreateRequest:
    project: str
    summary: str
    description: str

    def to_json(self) -> str:
        return json.dumps({ "fields": {
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
            "issuetype": {
                "name": "Task"
            }
        } }, indent=4)