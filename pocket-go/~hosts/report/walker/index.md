---
crate: crate.6FBAE742343AC3A5
title: strange happenings logbook
log-type: strange happening
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
