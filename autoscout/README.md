# AutoScout

Monitors [auto24.ee](https://www.auto24.ee) for used car listings, evaluates them
with Claude AI, and produces a ranked list of cars worth seeing in person.

Built for a specific use case: finding a reliable, low-maintenance petrol car in
Estonia (Toyota, Lexus, Honda, Mazda) with the lowest total cost of ownership.

## How it works

```
SCRAPE → INGEST → DIFF → SCREEN → EVALUATE → RANK → NOTIFY
```

1. Scrapes auto24.ee search results for configured filters
2. Parses listing pages, downloads photos
3. Detects new and changed listings
4. Quick AI screen (Haiku) rejects obvious mismatches
5. Full AI evaluation (Sonnet + Vision) scores remaining listings
6. Produces ranked list, pushes top finds via Telegram

## Docs

- [Project plan](docs/plan.md) — requirements, architecture, schema, config
- [Research](docs/research.md) — car knowledge base, platform details, sources
