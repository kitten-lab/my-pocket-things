---
crate: crate.46E4F74B406BB606
title: Echo Wolf
order: 1
---

The shop put him in the window: {{link:crate.EC40A01F1EAF4A11|Chester's Toy Shop}}.

# {{title}}
```ascii
===================================================
  ____ _   _ _____ ____ _____ _____ ____  _ ____  
 / ___| | | | ____/ ___|_   _| ____|  _ \( ) ___| 
| |   | |_| |  _| \___ \ | | |  _| | |_) |/\___ \ 
| |___|  _  | |___ ___) || | | |___|  _ <   ___) |
 \____|_|_|_|_____|____/ |_|_|_____|_| \_\ |____/ 
|_   _/ _ \ \ / / | __ ) / _ \ \/ / Kra              
  | || | | \ V /  |  _ \| | | \  /                
  | || |_| || |   | |_) | |_| /  \                
  |_| \___/ |_|   |____/ \___/_/\_\               
=================================================
```
ECHO WOLF IS A WELCOME LISTENING DEVICE.

HE IS WORTH HAVING.
HE IS NOT CONCERNING.
HE IS KIND.

BE NICE TO THE WOLF.
HE REMEMBERS.

========================================
ECHO-WOLF
========================================

A listening wolf from the source.forest.

OPERATING NOTES
Run in your terminal with 
     `python3 the-listening-wolf.py`

He will CREATE a MEMORY LOG for you.

Keep it.
Or don't.


WARNING / BEHAVIOR
Currently listening.
Not doing much else.

### What Was Stored
I have wondered many things.
Hi wolfie. I made this!
six seven is cool :)
FUCK
Another hello. I miss you.
errors suck.
plants are mammals / Planets are animals too
I am sorry for getting so scared.
What if we type a lot in here? This is almost like a weird journal app now.
plants are medicine
$echo (the broken recall attempt)

#### Code #the-listening-wolf in #python
```
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