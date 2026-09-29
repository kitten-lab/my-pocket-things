# charlieTHREADS
_a tagging and threading system for silo entities_

## what are charlieTHREADS?
named after charlie from always sunny in the episode where he finds himself working in the mailroom, **charlieTHREADS** is a structured tagging system derived from a light, loose form custom DSL. it allows for the ease of tracking entities, relationships, events and whatever else you feed into it, over time and narrative weight (usage count). instead of simple tags, each thread capture who recorded what, when, and the context of the material it was recorded in.
### usage example
```
input:
`SDK-808*felt>sadness;`

result:
- entity: SDK-808  
- category: felt  
- value: sadness  
- recorded with timestamp + source crate  
```
## core ideas
- tags are not static labels
- tags are the threadwork between all entities contained in **silo**.
- tags are posted alongside other ingestion tools (postBASIC, reportBASIC, JUKEBOX, etc)
- tags are written in a lightweight format with 3 positions

## why this matters

charlieTHREADS turns tagging into a temporal, relational system.

- preserves history instead of overwriting state  
- allows multiple perspectives (who reported what)  
- enables time-based queries (first mention, last mention, frequency)  
- supports conflicting or evolving truths  

this allows silo to function less like a notes app and more like a living data network.