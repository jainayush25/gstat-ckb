---
name: drawn-explainer-video
description: Make vertical (9:16) short-form "hand-drawn company explainer" videos in the style of the Setter-30 / top-private-tech-companies series. A marker infographic is drawn on paper on a cutting mat, in sync with a voiceover, with burned-in captions, a following camera and a full-sheet reveal at the end. Use whenever the user wants a Reel/TikTok/Short that explains a company, startup, product, market or business model with a whiteboard / marker / sketch / doodle / hand-drawn infographic look, or asks to "make a video like these" about any company (e.g. "make one for Apple/Stripe/OpenAI"), or wants to reverse-engineer and reproduce this explainer format.
---

# Hand-drawn company explainer videos

This skill covers the whole job: research the company, write a ~2-minute script in the
format's beat structure, lay out one infographic sheet, and render an MP4 with
`scripts/render.py` (narration via Piper TTS, Whisper-timed captions, a pen that draws each stroke
along with the narration, marker sounds and a soft pad).

`references/format-breakdown.md` explains how the original format works (beats, visual
grammar, caption style). Read it before writing a new script.
`examples/apple.json` is a complete, working spec you can copy.

## 0. Setup (once per machine)

```bash
bash scripts/setup.sh            # pip deps, 4 OFL fonts, Piper voice -> assets/
```
You also need `ffmpeg`. If `import skia` fails with `libEGL.so.1`, run `apt-get install -y libegl1`.
Whisper is optional. Without it, pass `--no-whisper` and captions are timed proportionally.
Microsoft edge-tts does **not** work behind proxies that block WebSockets. Use Piper.

## 1. Research (facts must be right)

Collect 6–10 concrete, checkable facts: founding year and founders, the original problem,
the key product, the contrarian decision, 2–4 revenue data points for a chart, the
valuation or market cap, money raised and investors, and one big headline number. Use web
search and give dates for anything that changes (valuation, market cap). Round numbers in
speech ("more than four trillion"). Keep the exact numbers on the sheet. If a fact is
reported but not confirmed, say "reportedly".

## 2. Script: the 8-beat formula (300–360 words ≈ 2:00–2:20)

1. **Hook** (cold open, 1–2 sentences). A surprising claim or reframe: "X is the company everyone
   thinks they understand. But its real business isn't…"
2. **Series card** (one sentence): "This is part N in my series explaining…"
3. **The status-quo problem**, with something simple to draw.
4. **Origin**: year, founders, first product.
5. **The twist / contrarian move**: "Here's the part most people miss…" / "Then they made a strange decision."
6. **Why it compounds now**: the flywheel, moat or AI tailwind, with an everyday analogy.
7. **Numbers**: a growth chart, margins, valuation, investors.
8. **Kicker**: one line that calls back to the main metaphor. No call to action.

Write the way people talk. Keep sentences short and put a number every 10–15s. Each beat is
one or two sentences, so there are 14–20 beats in total. Each beat should name something that
can be drawn.

## 3. Lay out the sheet (paper = 1400 x 2000 units)

Sketch the finished poster before writing any coordinates:
- **Top band (y 50–300)**: the logo/wordmark at the top center, a revenue figure in one corner, and a
  `box3d` valuation callout in the other corner (vertical label).
- **Upper middle (y 330–660)**: the origin or problem story, in left and right halves.
- **Band (y 720–860)**: a timeline if the story needs one.
- **Center (y 900–1600)**: the main diagram (stack/layers/flow/map), with supporting icons in
  the left and right columns.
- **Bottom (y 1640–1960)**: two charts side by side (growth plus a comparison).
Keep about 60 units of margin. Text sizes: titles 54–64, labels 24–36, small notes 20–24.
Hand text is upper-cased automatically.

Always render the layout and **look at it** before rendering the video:
```bash
python3 scripts/render.py spec.json --no-whisper --layout /tmp/layout.png
```
Fix overlaps, then check some animated frames (camera + pen + captions):
```bash
python3 scripts/render.py spec.json --no-whisper --stills 2,10,30,60 --stills-dir /tmp/st
```

## 4. Render

```bash
python3 scripts/render.py spec.json -o out.mp4      # about 2–4 min of CPU for a 2-min video
```
After rendering, check the narration by transcribing it with Whisper. Look for any words the
TTS got wrong and add a `tts` override for those beats (years and `$` amounts are the usual
problems).

## Spec reference

Top level: `voice` (Piper voice name in assets/voices or a path to an .onnx), `speed` (Piper
length-scale; 0.9 is lively), `paper` [w,h], `fps` (30), `caption_chars` (26),
`caption_size` (40), `caption_y` (0.765), `music_gain` (0.045), `scratch_gain` (0.05),
`mat`, `paper_color`, `tape`, `seed`, `gap` (seconds between beats), `tail`.

Beat fields:
- `say`: the caption text, and also what gets spoken. `tts`: optional pronunciation override
  (for example `"nineteen ninety seven"`).
- `type`: `draw` (default) | `cold_open` (pans over the finished sheet) | `card` (ranked list:
  `kicker`, `title`, `columns`, `col_x`, `rows`, `highlight` index).
- `draw`: the elements, drawn one after another across the narration. An element's `span`: [a,b]
  pins it to a fraction of the beat, and `speed` scales its share of the time.
- `cam`: `"auto"` (frames this beat's elements) | `"full"` | `[x,y,w]` | `[[x,y,w],[x,y,w]]`
  to pan or zoom across the beat. `w` is the visible width in paper units, and the height is
  w*16/9. Use a 2-keyframe cam on the last beat to zoom out to the full sheet (`w` ≈ 1.14×paper width).
- `hold`: extra seconds after the narration. `lead`: delay before the voice starts.

Elements (paper coordinates; colors are palette names or `#hex`. Palette: ink blue cyan
green lime purple orange yellow red gray silver brown pink teal navy):

| type | fields |
|------|--------|
| `text` | x, y (vertical center), text (`\n` ok), size, font `hand`/`marker`/`bold`, align, rotate, color, caps |
| `line` / `arrow` / `curve` | pts [[x,y],…], arrow `end`/`start`/`both`/`none`, dashed, smooth |
| `rect` | x, y, w, h, r (corner), fill, fill_only, label, label_size, direction `right`/`up` |
| `circle` / `ellipse` | cx, cy, r or rx/ry, fill, label |
| `poly` | pts, fill, closed |
| `highlight` | x, y, w, h, fill (yellow): a highlighter swipe |
| `box3d` | x, y, w, h, d, fill, label, label_rotate (−90 for a vertical valuation label) |
| `bars` | x, y, w, h, values, labels, max, value_fmt (`"${v}B"`), fill, colors, title, bar_ratio |
| `apple_logo` | cx, cy, size, fill, leaf_fill |
| `phone` | x, y, w, h, fill (screen), apps (true = icon grid), label |
| `laptop` | x, y, w, h, fill, base_fill |
| `watch` | cx, cy, s, fill, strap_fill, screen_fill |
| `cloud` | cx, cy, w, fill, fill_alpha, label |
| `coin` | cx, cy, r, fill, label |
| `wall` | x, y, w, h, fill, brick_w, brick_h |
| `door`, `star`, `xmark`, `brace` | see render.py `build_ops` |

Common fields: `color` (outline, default ink), `width` (3.2), `wobble` (hand jitter, 1.2),
`fill_alpha`. Draw outlines first and fills after; fills multiply over the ink like real
markers. To add a new icon, add a branch in `build_ops` that returns `StrokeOp`, `FillOp`
and `TextOp` objects.

## Notes and limits

- No real presenter or hand footage. The `cold_open` beat stands in for the on-camera hook.
  If the user has a face-cam clip, overlay it on the first seconds with ffmpeg.
- Company logos: draw a simple outline of the company's mark or write the wordmark in the
  `marker` font. Don't copy another creator's series branding (e.g. "The Setter 30"). Name the
  series card after the user's own series.
- Check every number on screen against a source and keep the sources in your reply.
