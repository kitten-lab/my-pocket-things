---
crate: crate.ED39600A4D34EB68
title: omens logbook
log-type: omen
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
