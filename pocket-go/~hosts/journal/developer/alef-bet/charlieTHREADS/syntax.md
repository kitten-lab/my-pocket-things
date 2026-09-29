# syntax shapes
tags begin as a lightweight custom DSL.  
a raw string-example: `NEWS*MEDIA>SKYLINE-NEWS;SKYLINE-NEWS*section>updates;`
### usage example
```usage
input:
`SDK-808*felt>sadness;`

result:
- entity: SDK-808  
- category: felt  
- value: sadness  
- recorded with timestamp + source crate  
```
### parser
``` charlieTHREADS DSL format
`A*B>C;`

- `A` = source entity  
- `*` = relationship separator  
- `B` = category / context  
- `>` = directional link  
- `C` = target entity  
- `;` = statement terminator
```

