---
crate: crate.E9792ECDA6C043A4
title: body knowings logbook
log-type: body knowing
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
