# v0.2.16
# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

from genlayer import *

json = __import__("json")


class Contract(gl.Contract):
    counter: u256
    stored_text: str

    def __init__(self):
        self.counter = u256(0)
        self.stored_text = ""

    @gl.public.write
    def increment_and_store(self, text: str) -> str:
        self.counter = self.counter + u256(1)
        self.stored_text = text
        return json.dumps(
            {
                "counter": int(self.counter),
                "stored_text": self.stored_text,
                "status": "ok",
            },
            sort_keys=True,
        )

    @gl.public.view
    def get_state(self) -> str:
        return json.dumps(
            {
                "counter": int(self.counter),
                "stored_text": self.stored_text,
            },
            sort_keys=True,
        )
