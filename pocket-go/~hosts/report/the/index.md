---
crate: crate.45ADE67F7E725523
title: teehee secrets logbook
log-type: teehee secret
---

{{injector}}
{{hidden:frontmatter}}
  {{text:title}}
{{/hidden}}
{{textarea:what-happened}}
{{text:when|when (blank = now; unix or date ok)}}
{{hidden:lib}}
  type: logger
  class: {{log-type}}
  sub-class: {{text:type}}
  posted on {{time:when}}
{{/hidden}}
{{hidden:tps}}
  created: {{time:when}}
{{/hidden}}
{{/injector}}
