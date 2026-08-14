# FAQ

### Is this open source?
No. Canvest is a commercial product in development. This repository is a public
**preview** — documentation, diagrams, and screenshots — so you can understand what
Canvest does and how it works. The engine, scoring logic, prompts, and tuned
parameters are not published.

### Can I run it?
Not from this repository — there's no application code here. If you're interested in a
demo or access, see below.

### What do the screenshots show?
A local demo instance populated entirely with **synthetic data**. The artists, titles,
listings, prices, and comparables are invented for illustration. No real auction data
appears anywhere in this repo.

### Why won't you share the exact rubric, prompts, or thresholds?
Those are the tuned core of the product — the part that took real work to get right and
that a competitor could copy directly. The methodology is shared openly; the
specifics that constitute the edge are kept private.

### What's the business model?
Canvest is being developed toward a commercial offering. Details are still taking shape
— reach out if you'd like to talk.

### How is this different from "just using an AI to price art"?
Two things. First, the **evidence gate**: Canvest refuses to recommend a bid unless a
*verified, realized* sold comparable backs the number, so it doesn't get talked into a
purchase by an optimistic estimate. Second, the **learning loop**: it records what
actually sold and calibrates against it, so accuracy compounds over time instead of
staying static.

### Is the data collection ethical / polite?
Yes, by design. Capture is human-in-the-loop and there's no high-frequency scraping;
price checks are infrequent and lightweight.

### Who built this?
Canvest was designed and built end to end by **Joseph Cintron** — the methodology, the
data model, the analysis pipeline, and the web app. It's shared here as a portfolio case
study as well as a product preview.

### How do I get in touch?
Reach out via the contact details on my GitHub profile
([github.com/JosephCintron](https://github.com/JosephCintron)) — for research
opportunities, collaboration, a demo, or early access.
