# Comparison

| Aspect | Typical grown-over-time setup | This repo |
|--------|------------------------------|-----------|
| Layer 1 trigger | `stop` hook | `sessionStart` scan |
| Layer 2+3 trigger | Manual ask or soft rule | Auto on first message + manual |
| Orchestrator | Multiple scripts + queue file | `update_wiki.py` |
| State | Complex freshness registry | `wiki_state.json` |
| Content | Real project history | Fictional examples |
