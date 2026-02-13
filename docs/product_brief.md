# Product Brief: Interactive Books

## The Problem

Readers own hundreds of books but interact with them passively. Finding a specific argument, recalling a detail, or exploring themes means flipping through pages or relying on memory. The tools that could help — LLMs — are locked out of existing reading platforms.

Apple Books, Kindle, Google Play Books, and Kobo offer no way to use an LLM with the books you've purchased. These platforms treat books as static files to be displayed, not as knowledge to be queried. Readers can highlight and take notes, but they can't ask questions, get summaries, or have conversations about what they've read.

This isn't a technical limitation. It's a product gap. LLMs are already capable of high-quality retrieval-augmented generation over long documents. The incumbents haven't moved because of licensing complexity, platform inertia, and misaligned incentives — their business is selling books, not making them more useful after purchase.

## Prior Art

Several products occupy adjacent spaces:

| Product | What it does | How we differ |
|---------|-------------|---------------|
| **Google NotebookLM** | Upload docs, get AI-generated summaries and Q&A | Cloud-only, no page-awareness, no spoiler control, Google controls your data |
| **ChatPDF / Humata** | Upload a PDF, chat with it | Web-based, no reading position tracking, no local processing, subscription model |
| **Readwise Reader** | Read-later app with AI summaries | Reading tool first, AI second; no deep Q&A, no page-scoped retrieval |
| **ChatGPT / Claude** | General-purpose LLM chat | No access to the actual book text — answers are from training data, not your copy |

The gap: none of these are **local-first**, **page-aware**, or **spoiler-safe**. None let you bring your own LLM. None treat the book as a knowledge base scoped to your reading progress.

## The Opportunity

Interactive Books fills this gap — a local-first app that gives readers LLM-powered access to books they own.

**Start small:** A local-only app where readers upload their own book files and chat with them. No server, no subscription, no data leaving the device (except LLM API calls). The reader owns their data.

**Prove the value:** Once people experience interactive reading — asking questions, getting spoiler-free summaries scoped to their reading position, finding passages instantly — static reading feels broken. The habit sticks.

**Expand later:** The local tool is the wedge. Once the interaction model is proven, the product can grow into a broader platform — roughly in this order:

1. **Curated collections** — interactive reading lists for courses, book clubs, research (lowest friction, builds on existing product)
2. **Shared annotations and Q&A** — community knowledge layers on top of books (requires accounts, but no publisher deals)
3. **Publisher integrations** — books ship with interactive capabilities built in (requires partnerships)
4. **Marketplace** — a distribution channel where "interactive" is the default, not a feature (requires all of the above)

## Why Now

- LLMs are good enough for book-quality RAG with accurate citation
- Embedding models are cheap, fast, and available locally (Apple NaturalLanguage, Ollama)
- Local-first apps are a viable architecture — no server costs, no scaling problems
- Incumbents are structurally slow to adopt this (licensing, platform politics, ad/subscription models)
- Readers already use ChatGPT to discuss books — but without access to the actual text, answers are generic and unreliable

## Business Model

v1 is free. The goal is to validate the interaction model, not to monetize. Users bring their own API keys and pay their own LLM costs.

Revenue comes later, once the product has proven value. Possible directions include a paid app (one-time purchase or subscription for premium features), a marketplace take-rate, or publisher licensing. The right model depends on which expansion path gains traction first.

## What We're Building (v1)

A local-only iOS/macOS app and Python CLI that lets readers:

1. Upload books (PDF, TXT)
2. Set their reading position (page-aware, spoiler-free)
3. Ask questions and get answers grounded in the actual text, with page citations
4. Choose their LLM provider (Anthropic, OpenAI, or local via Ollama)

Everything runs on-device or via direct API calls. No backend. No account. No data collection.

See [Product Requirements](product_requirements.md) for the full feature spec.
See [Technical Design](technical_design.md) for architecture and implementation details.

## Who It's For

Individual readers who want more from the books they already own. Early adopters who are comfortable with API keys and local apps. Students, researchers, and professionals who read deeply and need to recall, compare, and synthesize across books.

v1 is not for casual readers or people who want a turnkey consumer experience. That comes later, after the core interaction model is validated.
