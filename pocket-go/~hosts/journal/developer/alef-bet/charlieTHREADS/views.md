all tags are parsed into structured json and then projected into multiple lookup systems depending on context:
### - by chestersCRATE payload:
```
        "tags": {
            "news": {
                "media": [
                    "skyline-news"
                ]
            },
            "skyline-news": {
                "section": [
                    "updates"
                ]
            }
        },
```


and the sent out to be threaded into several reports (examples are various contexts, not all the example string):
### - by single-word lookup
```
{
    "CABINET": {
        "financial-plan": {
            "METADATA": {
                "GRAVITY": 1,
                "INGEST": {
                    "FIRST": 1777159009,
                    "LAST": 1777159009
                },
                "EVENT": {
                    "FIRST": [],
                    "LAST": []
                },
                "LAST_USAGE": {
                    "1739984014": [
                        "symbolcraft"
                    ]
                }
            },
            "SHELF": {
                "symbolcraft": {
                    "METADATA": {
                        "GRAVITY": 1,
                        "INGEST": {
                            "FIRST": 1777159009,
                            "LAST": 1777159009
                        },
                        "EVENT": {
                            "FIRST": [],
                            "LAST": []
                        },
                        "LAST_USAGE": {
                            "1739984014": [
                                "docs"
                            ]
                        }
                    },
                    "BIN": {
                        "docs": {
                            "METADATA": {
                                "GRAVITY": 1,
                                "INGEST": {
                                    "FIRST": 1777159009,
                                    "LAST": 1777159009
                                },
                                "EVENT": {
                                    "FIRST": [],
                                    "LAST": []
                                }
                            },
                            "INSTANCES": {
                                "1739984014": {
                                    "DW": [
                                        "crate.26570475582EB59D"
                                    ]
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
```
### - by entity 
```
{
    "VEN": "data-forestry",
    "GRAVITY": 4,
    "ALIAS": [],
    "NOTES": [],
    "METADATA": [],
    "SHELF": {
        "purpose": {
            "GRAVITY": 4,
            "BIN": {
                "ingest-material": 1,
                "searchable": 1,
                "storage": 1,
                "silo": 1
            }
        }
    }
}
```
### - by insect (intersections)
"insect" views show overlapping relationships across entities—where multiple threads converge into shared meaning.
```
{
    "VEN": "detective-case_work",
    "GRAVITY": 41,
    "METADATA": [],
    "SHELF": {
        "slots": {
            "GRAVITY": 41,
            "BIN": {
                "illustrations": 2,
                "main_game": 3,
                "functionality": 5,
                "intentions": 10,
                "theme": 2,
                "detective-for-hire": 3,
                "anticipation": 1,
                "resolution": 1,
                "two-act": 1,
                "investigation": 1,
                "story-phases": 1,
                "trope_detective": 1,
                "office": 2,
                "symbols": 1,
                "solutions": 2,
                "client-cases": 2,
                "environment": 3
            }
        }
    }
}
```
### - and by relations 
```
{
    "VEN": "partnerships",
    "GRAVITY": 2,
    "METADATA": [],
    "SHELF": {
        "symbolcraft": {
            "GRAVITY": 2,
            "BIN": {
                "opportunities": 1,
                "goals": 1
            }
        }
    }
}
```

