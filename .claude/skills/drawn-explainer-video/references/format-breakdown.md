# Format breakdown: the "hand-drawn company explainer" short

I worked this out from three reference videos (Databricks, Crusoe and VAST Data). They are
part of a creator series explaining top private tech companies. All three are 9:16,
720x1280, between 2:09 and 2:21 long, with 300–380 spoken words (about 2.6 words per second).

## 1. Story structure (same in all three)

| # | Beat | Time | Databricks | Crusoe | VAST Data |
|---|------|------|-----------|--------|-----------|
| 1 | **Hook**: a surprising claim, said to camera over the *finished* drawing | 0–6s | "the hardest company I've tried to explain yet" | "turned that problem into a super surprising advantage" | "$30B company that doesn't show up on our list" |
| 2 | **Series/credibility card**: a ranked-list screenshot with the company's row highlighted | 3–10s | "part seven in my series" | "one of the most valuable private tech companies" | (skipped; the hook mentions the list instead) |
| 3 | **Status-quo problem**, drawn simply | 10–30s | warehouse vs lake, two systems | grid full, 7-year wait | AI as a 5-layer cake |
| 4 | **Origin**: year, founders, first product | ~30–50s | 2013, Berkeley, Spark | 2018, Chase & Cully, flare gas → Bitcoin | valued $30B, Rule of 40 |
| 5 | **The contrarian move / insight** | ~50–70s | "Then they made a strange decision": open-sourced it | "moved the demand to the power" | AI operating system, analogy (TV show) |
| 6 | **Why now / AI tailwind** | ~70–100s | ChatGPT → utility bill | OpenAI RFP, Abilene | real-time inference |
| 7 | **The numbers**: revenue curve, valuation, raise, investors, IPO talk | ~100–125s | $200M→$5.4B, $134B | $10B→$30B talks | NVIDIA, NASA, Pixar |
| 8 | **Kicker**: one line that calls back to a metaphor | last 5s | "...letting the oil flow freely" | "We'll see if this trapped energy play..." | "holding it all together" |

Script rules that show up in all three:
- Sentences are short and spoken. Lots of "Here's the crux", "Pretty solid business.",
  "It totally worked.", "The revenue growth is wild."
- At least one **analogy** that a non-technical viewer can hold onto (oil pipeline, utility bill,
  layer cake, TV recommendation).
- Every 10–15 seconds there's a **concrete number**: a year, $ amount, multiple or wait time.
- There's **one twist** ("Then they made a strange decision.").
- The ending comes back to the main metaphor in a single sentence. No call to action.

## 2. Visual grammar

- **Top-down camera** on one sheet of white (often dot-grid) paper, held with lime/yellow
  washi tape at the top and bottom edges, on a **dark self-healing cutting mat** (white grid lines,
  dotted sub-grid, 45° guide lines).
- One infographic is built up over the whole video. Each sentence adds the thing it talks about.
  Nothing is erased.
- Layout: the **company logo/wordmark is centered at the top**. A **valuation callout** sits in a
  top corner (an extruded 3D box with a vertical "$134B" label, or a bar chart), and the **main
  diagram** fills the middle, so the finished sheet reads top to bottom like a poster.
- Drawing style: black fineliner outlines that are slightly wobbly, **ALL-CAPS architect
  lettering**, then **alcohol-marker fills** in flat saturated colors (cyan, lime green,
  lavender/purple, orange, yellow, red, warm gray) with visible streaks. Plastic stencils are
  used for circles and boxes. Isometric 3D boxes and slabs are everywhere (buildings, platforms,
  cake layers, bars).
- Diagram vocabulary: stacked layers or platforms, isometric bar charts, simple line/step charts,
  a simple map silhouette, labelled arrows, dashed connector lines, curly braces, logos of
  partners drawn small, cartoon objects (lake, oil pump, TV, cake).
- **Camera** stays close on the area being drawn and pans/zooms to each new area. At the end it
  **pulls back to reveal the whole sheet** (and sometimes the paper is picked up).
- A hand with the pen is always in frame while something is being drawn. The footage is sped up
  so the drawing keeps pace with the voice.

## 3. Captions and audio

- Burned-in captions: **white bold geometric sans** (Montserrat/Proxima-like), about 34–40px on
  720 wide, a soft dark shadow, centered at about **76% of the frame height**, **2–6 words per
  phrase**, one phrase at a time, and breaking at punctuation.
- Voiceover: one friendly, fast, conversational narrator. There's quiet ambient sound and
  occasional marker scratching. No big music cues.

## 4. Recreating it automatically

`scripts/render.py` does a synthetic version of this:

| Original | Recreation |
|----------|------------|
| Presenter hook over the finished art | `cold_open` beat: a slow pan across the finished sheet with the hook in captions |
| Ranked list screenshot | `card` beat: a document-style list with an animated highlighter on one row |
| Hand + pen drawing in real time | Each stroke is revealed along its length, text is written left to right, fills wipe in like marker strokes, and a rendered pen follows the drawing tip |
| Sped-up drawing matched to the voice | The drawing elements in each beat are spread across that beat's narration |
| Camera following the pen | Auto camera frames the bounding box of each beat's elements, eases between beats, and drifts in slowly |
| Final pull-back | Last beat `cam: [[zoomed],[full]]` |
| Captions | Piper TTS → Whisper word timestamps → 2–6 word phrases |
| Marker sounds | Band-passed noise wherever the pen is moving, plus a soft pad |
