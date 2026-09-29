# Ven isContainer System

There is one structural property that ensures the world can be made:
`isContainer`

Which means the world graph is simply:
`VEN → contains → VEN`

**That’s it.**

## The Container Logic Is the Secret Sauce

All things contain other things:

> room contains bed  
> quest contains event  
> mira contains lipstick

Notice something elegant here.
We are using the **same structural relationship** for:

|Domain|Relationship|
|---|---|
|space|room → bed|
|narrative|quest → event|
|inventory|mira → lipstick|
|world structure|district → tavern|

So containment becomes a **universal relationship**.

Producing complex entity types become trivial:
### A room
	ven.Room_221  
	  prop: isContainer=true  
	  contains:  
	      ven.Bed_03  
	      ven.Table_02  
	      ven.Mira_01

### Mira
	ven.Mira_01  
	  prop: isCharacter=true  
	  contains:  
	      ven.Lipstick_04  
	      ven.MemoryGraph

### A quest
	ven.Quest_VampireNight  
	  prop: isContainer=true  
	  contains:  
	      ven.Event_Intro  
	      ven.Event_Hunt  
	      ven.Event_Reveal

### A world
	ven.World_Skyline  
	  prop: isContainer=true  
	  contains:  
	      ven.District_A  
	      ven.District_B  
	      ven.District_C

## It Also Works for Abstract Things

Because VENs can represent **concepts**, you can do stuff like:

### Emotions
	ven.Mira  
	  contains:  
	      ven.Fear

### Memories
	ven.Mira  
	  contains:  
	      ven.Memory_TavernFire

### Culture
	ven.District_A  
	  contains:  
	      ven.Symbol_RedRose

Now the narrative engine can reason about **ideas the same way it reasons about objects**.

Because containers can contain containers:

```
World  
  contains District  
District  
  contains Tavern  
Tavern  
  contains Room  
Room  
  contains Mira
```

You automatically get **spatial hierarchy**.

And because quests are containers:

```
Quest  
  contains Event  
Event  
  contains Action
```

You also get **narrative hierarchy**.

Same structure. Two different domains.

world engine is basically a **living graph** like this:

```
World
 ├ District
 │   ├ Tavern
 │   │   ├ Mira
 │   │   │   ├ Lipstick
 │   │   │   └ Memory
 │   │   └ Bed
 │   └ Market
 └ Quest
     ├ Event1
     └ Event2
```

Everything in the universe is just **nodes connected by relationships**.

The structure screams **graph database**.


Your model also solves **scope** automatically.

Example:

Room  
  contains Mira

means Mira is **in that room**.

Mira  
  contains lipstick

means lipstick is **in her inventory**.

The engine doesn’t need a separate "inventory system" or "location system".

Containment **is both**.
---