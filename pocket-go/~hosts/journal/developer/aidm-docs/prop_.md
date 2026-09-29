---
child of: none
Definition: Default chain of properties that apply to ALL entities
Usage: ven10{prop*}
Parent Type: namespace
---

| `field name`       | `usage`                                        | `description`                                                                                                                      | `Type`                                                        |
| ------------------ | ---------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------- |
| `prop_isPrime`     | `K_prop_isPrime`                               | `Entity is Prime class.`<br><br>`Additional fields are provided when K_propIsPrime=true`<br><br>`I.E. Human is K_propIsPrime=True` | `Boolean`                                                     |
| `prop_canIns`      | `K_prop_canIns`<br>`ven_prop_canIns`           | `Exact copies of the entity can be made, I.E. soliders or clones of entities`                                                      | `False(disabled)` <br>`allTrue`<br>`onlyK`<br>`define_perIns` |
| `prop_canGen`      | `K_prop_canGen`<br>`ven_prop_canGen`           | `The entity can birth new entities which are not itself. I.E. Hybrid instancing (new patterns) or birthing children`               | `False`<br>`True`<br>`define_perIns`                          |
| `prop_canChange`   | `K_prop_canChange`<br>`ven_prop_canChange`     | `The entity can change from one entity to another`                                                                                 | `False`<br>`allTrue`<br>`onlyK`<br>`define_perIns`            |
| `prop_isContainer` | `K_prop_isContainer`<br>`ven_prop_isContainer` | `Entity can contain other entities`                                                                                                | `False`<br>`True`<br>`define_perIns`                          |
| `prop_canMove`     | `K_prop_canMove`<br>`ven_prop_canMove`         | `Entity can move between entities`                                                                                                 | `False`<br>`True`<br>`define_perIns`                          |
| `prop_canSpeak`    | `K_prop_canSpeak`<br>`ven_prop_canSpeak`       | `Entity uses spoken language capabilities and can self advocate.`                                                                  | `False`<br>`True`<br>`define_perIns`                          |
| `prop_canAIven`    | `K_prop_CanAIven`<br>`ven_prop_canAIven`       | `Entity can be used by AIDM as playable in quests`                                                                                 | `False`<br>`True`                                             |
| `prop_canMulti`    | `K_prop_canMulti`<br>`ven_prop_canMulti`       | `Entity can temporarily instance itself`                                                                                           | `False`<br>`True`<br>`define_perIns`<br>                      |
| `prop_canEffect`   | `K_prop_canEffect`<br>`ven_prop_canEffect`     | `Entity can effect other entities who canChange`                                                                                   | `False`<br>`True`<br>`define_perIns`                          |
| `prop_isTimebound` | `K_prop_isTimebound`<br>`ven_prop_isTimebound` | `Entity is locked in linear time.`                                                                                                 | `False`<br>`True`<br>`define_perIns`                          |
