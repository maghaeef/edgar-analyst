# edgar-analyst

An agentic system that produces analyst-style memos on US public companies by autonomously reading their SEC filings.

Given a ticker, the agent fetches the company's most recent 10-K and 10-Q from EDGAR, identifies a peer group, performs year-over-year and peer-relative analysis on the financials and narrative sections (Risk Factors, MD&A), and outputs a structured memo with citations back to the source filings.

## Why

Equity analysts spend a large share of their time on the mechanical parts of filing review: pulling documents, extracting line items, comparing them to last year, comparing them to peers, and writing up the deltas. This project automates that mechanical layer so the analyst's attention can go to judgment and narrative. The output is intentionally a *memo* rather than a raw data dump — the goal is decision-relevant text, not a dashboard.

## What "agentic" means here

The system is not a single LLM call. It is a tool-use loop in which Claude plans, calls tools (EDGAR fetch, financial-statement parser, peer lookup, diff), reads the results, and decides what to do next until it has enough information to write the memo. The loop, the tool definitions, and the orchestration are implemented directly against the Anthropic SDK — no third-party agent framework — so the mechanism is transparent and inspectable.

## Quickstart

```bash
git clone https://github.com/maghaeef/edgar-analyst.git
cd edgar-analyst
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # then fill in ANTHROPIC_API_KEY and SEC_USER_AGENT
python -m edgar_analyst AAPL
```

The agent will stream its reasoning and tool calls to the terminal and write the final memo to `out/AAPL_<date>.md`.

## Configuration

Two environment variables are required:

- `ANTHROPIC_API_KEY` — your Anthropic API key.
- `SEC_USER_AGENT` — SEC EDGAR requires a User-Agent header identifying the requester (`"Your Name your@email.com"` is sufficient). Requests without one are rejected.

## Project layout

```
src/edgar_analyst/
  agent.py         # the tool-use loop
  tools/           # tool implementations (edgar fetch, parsers, peers, diff)
  models.py        # pydantic schemas for tool inputs/outputs
  prompts.py       # system prompt and memo template
  __main__.py      # CLI entrypoint
tests/             # unit tests for tools (no live API calls)
```

## Success criteria

The system is considered successful if, for an arbitrary large-cap US ticker, it produces a memo that:

1. Is grounded — every quantitative claim cites a specific filing and section.
2. Is comparative — both YoY and peer-relative deltas appear, not just point-in-time figures.
3. Is decision-relevant — the memo ends with a "what changed and why it matters" section, not a recap.
4. Is reproducible — running the same ticker twice yields substantively the same memo (modulo LLM nondeterminism in phrasing).
5. Costs less than $0.50 in API spend per run.

These criteria are checked manually on a small test set of tickers (see `tests/manual_eval.md`).

## Limitations and honest caveats

- US public companies only. EDGAR is a US-only system.
- Foreign private issuers (20-F filers) and SPACs are out of scope for this version.
- Peer identification uses SIC code matching plus a market-cap filter; it is heuristic, not curated.
- The agent does not access market data (prices, multiples) beyond what is in the filings themselves. Adding a price tool is a natural extension.
- LLM hallucination risk is mitigated by tool-use grounding, but not eliminated. Treat memos as drafts.

## External systems and data

- **SEC EDGAR** (`data.sec.gov`) — primary data source. Public, free, rate-limited to 10 req/sec. Cached locally under `data/cache/` to stay well under the limit.
- **Anthropic API** — `claude-sonnet-4-6` for the agent loop. Sonnet is Anthropic's current model class for long-running agents and financial analysis, and it fits the project's cost budget. Opus 4.7 would yield higher-quality memos but at roughly 5× the cost.

No other external services are used. No API keys are required besides Anthropic.

## License

MIT. See `LICENSE`.