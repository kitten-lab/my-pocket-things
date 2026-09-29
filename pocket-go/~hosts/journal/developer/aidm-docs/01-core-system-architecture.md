# Core System Architecture
## Overview (notes)

### Meet AIDM

AIDM (pronounced like *Adam*) is an AI Agent responsible for the management and organization of sprawling narratives played within the structure of MIRA. AIDM stands for AGENIC INTERACTIVE DREAM MODERATOR.

### Meet MIRA
##### **One-law ontology** of [[MIRA]]:

**Everything is a [[VEN]].**

All attributes and functions of a ven emerge from **properties and dynamics**

	VEN
	  ├ properties
	  └ dynamics

[[EIDN]]’s world graph is a **uniform data model**.

In place of separate systems like:

	Item system  
	Character system  
	Quest system  
	World system  
	Event system

[[MIRA]] only has:

`VEN system

And meaning comes from properties:

	prop_isCharacter  
	prop_canMove  
	prop_canVend
	propContainer_capacity  
	prop_isSocial

So the engine doesn't need a thousand hard-coded types.

It just reasons about [[VEN]] relationships.

Structurally **everything is the same *object of potential***.

Only the **properties change the meaning**.

If you zoom way out, MIRA is basically:

```
*==============================*
 +----------------------------+
 \|     A graph of VENs      |/
  |           +              |
  |     property engines     |
  |           +              |
  |     dynamic rulesets     |
  |           +              |
 /|   narrative reasoning    |\
 +----------------------------+
*==============================*
```

**That’s the *dream machine*.**

### Diagram of Narrative Data Movement in MIRA

```diagram
Functional Actors Interaction
                                          +--------------------------+
                                          | ON EACH TURN             |
 +------+               +--------+        | EIIDN Recieves lastTurn  |
 |  pc  | <--actLoop--> |  aidm  |<<<<<   | EIVE Returns Narrative   |
 +------+               +--------+    |   | Suggestions              |
							|         |   +--------------------------+
							V         |
				+-----------------------+
	+----- <--> |    Reason/updateDB    | <--> -----+
	|		    +-----------------------+           |
	|                                               |
+-------+             +------------+              +------+
| eiidn | <--State--> |  Timeline  | <--Energy--> | eive |
+-------+             |    GDB     |              +------+
					  +------------+

```

## Core Component Terminology

The following terms define the primary functional actors within the AIDM system architecture. Each component represents a distinct responsibility in the simulation and narrative engine.
### Functional Actors:

#### pc (Player Character)
*An active player-controlled base-container within the system.*

The PC interacts with the world through an AIDM and controls one or more VEN entities.

#### AIDM (AI Dungeon Master)
*A player-aligned narrative intelligence that interprets world states.*

The AIDM manages tone and narrative progression for the **pc** based on data from EIDN and EIVE.

#### EIDN (Environment Inter/Intra Dependency Network)
*The entity-state coordinator responsible for managing the world state.*

The EIDN provides entity states and related narrative probabilities to AIDM, guiding narrative continuity and managing the canonical timeline of event.

#### EIVE (Emotional Intelligence Vector Environment)
*A subsystem that models energetic relationships between entities.*

The EIVE provides effective context to AIDM for narrative decision-making to ensure entity continuity.

### VEN (Virtual Entity Node)
*An entity instance within the game with its own properties, histories, and data graphs*

