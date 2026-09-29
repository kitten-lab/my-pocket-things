---
crate: crate.EC40A01F1EAF4A11
title: Echo Wolf
order: 1
cover: echo-wolf-box.png
hue: amber
deck: He is worth having.
get_the_code: GET THE CODE
get_the_code_href: /?h=chesters&p=toys/echo-wolf#code
fold_it: fold the instructions
fold_it_href: /?h=chesters&p=toys/echo-wolf
seen: BE.IMPORTED.TO
seen_href: /?h=to
---

{{div:.product-hero}}

{{img:echo-wolf-box.png|Echo Wolf — a welcome listening device}}

{{div:.pitch-card}}
{{.product-kicker}}CHESTER'S TOY SHOP · NOW IN THE WINDOW
# Echo Wolf
{{.lede}}He is worth having.

He is a welcome listening device. He is not concerning. He is kind. Be nice to the wolf. He remembers.

He comes from the source.forest. Chester found him in the back of a crate that was supposed to be sad, put a sticker on the box, and turned on the lights.

He will create a memory log for you. Keep it. Or don't. Currently listening. Not doing much else. That is the whole pitch. That is why people leave smiling.

{{div:.buy-row}}
{{span:.price-tag.is-stock}}IN STOCK
{{span:.price-tag}}ONE MEMORY
{{get_the_code}}
{{/div}}
{{/div}}

{{/div}}

{{div:.traits}}
{{div:.trait}}
**KIND**
He tilts his head. He does not judge the sentence.
{{/div}}
{{div:.trait}}
**LISTENS**
The wires hum. He leans forward. He writes it down.
{{/div}}
{{div:.trait}}
**REMEMBERS**
Say `$echo` when you want a thing back. He might. He is a toy.
{{/div}}
{{/div}}

{{div:.seen-on}}
as seen on {{seen}} · advertistment · $9.95/mo
{{img:chesters-toys-ad.png|the banner Chester bought}}
{{/div}}

{{div:.code-hatch#code}}
{{div:.code-lid}}
THE LISTENING WOLF · python3 the-listening-wolf.py · back of the box
{{/div}}
{{div:.fold-it}}
{{fold_it}}
{{/div}}

```python
import sqlite3
import random

def initialize_db():
    conn = sqlite3.connect("eidn-wolf.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	content TEXT
        )
    """)

    conn.commit()
    conn.close()

def save_message(text):
    conn = sqlite3.connect("eidn-wolf.db")
    cursor = conn.cursor()

    cursor.execute("INSERT INTO messages (content) VALUES (?)", (text,))

    conn.commit()
    conn.close()

def count_messages():
    conn = sqlite3.connect("eidn-wolf.db")
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM messages")
    count = cursor.fetchone()[0]

    conn.close()
    return count

def print_messages():

    conn = sqlite3.connect("eidn-wolf.db")
    cursor = conn.cursor()

    cursor.execute("SELECT TEXT FROM messages (content)")
    count = cursor.fetchone()[0]

    conn.close()
    return random.choice(count)

write_actions = [
    "The wolf writes it down.",
    "The wolf scratches the words into the log.",
    "The wolf tilts his head and records it.",
    "The wolf listens carefully and stores the memory.",
    "The wolf nods slowly and writes."
]

def run():
    print("The wires hum. The wolf leans forward.")

    initialize_db()

    while True:
        user_input = input("You: ")

        if user_input.lower() == "end":
            print("The wolf dissolves back into the wires.")
            break

        if user_input.lower() == "help":
            print("Only you can help yourself.")
        
        if user_input.lower() == "$echo":
            print_messages();

        save_message(user_input)

        total = count_messages()

        print(random.choice(write_actions) + f"\n'{user_input}' is recorded to the memory.")
        print(f"(Persistent memory size: {total})")

if __name__ == "__main__":
    run()
```

{{div:.code-note}}
Run it in a terminal. He will CREATE a MEMORY LOG. The bugs are part of the toy. Chester will not patch them. They are how he tilts his head.
{{/div}}
{{/div}}

{{div:.source-note}}
The original listening lives in {{link:crate.46E4F74B406BB606|the mausoleum}}. This is the window. That is the drawer.
{{/div}}

{{flip}}

{{div:.also-shelf}}
{{.shelf-label}}also on the shelf
{{files}}
{{/div}}
