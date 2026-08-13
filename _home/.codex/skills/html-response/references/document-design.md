# Adaptive document design

Build one coherent document from section-level decisions. The available components are a vocabulary, not page templates.

## Start with the information

For every section, identify its job before choosing its form:

- Explain causality or nuance with prose.
- Compare exact values or repeated fields with a table.
- Show a trend with a simple chart.
- Show sequence, hierarchy, or dependencies with Mermaid.
- Show implementation details with language-tagged code.
- Surface a decision with a verdict or callout.
- Surface a few headline quantities with metrics.

Prefer prose when a visual does not materially reduce reading effort. Mix forms within one document when their jobs differ.

## Document character

- Use a dense, minimalist document rather than an application shell.
- Omit navigation headers and sidebars.
- Keep the main canvas broad. Body paragraphs fill their container with natural left/start alignment; reserve narrow metadata for section headers.
- Use pink as the primary accent. Let semantic syntax colors appear inside code.
- Preserve comfortable rhythm across a long answer. Density means low framing overhead, not cramped text.
- Write enough context for the document to stand alone after the chat is gone.
- Place caveats near the claim or estimate they qualify.

The shared shell automatically provides the docs favicon, light/dark/system controls, Maple Mono code styling, syntax highlighting, and Mermaid interaction.

## Core markup

Use `<section class="section">` as the main unit:

```html
<section class="section">
  <div class="section-head">
    <h2>Section title</h2>
    <p>Compact context or units</p>
  </div>
  <p>Substantive explanation...</p>
</section>
```

The section component supplies a consistent gap between every direct child. Keep related content as direct section children (for example, a callout followed by a table) instead of compensating with one-off margins.

For a short section label or secondary context, keep it inside the header. The shared component controls its spacing and alignment:

```html
<section class="section">
  <div class="section-head">
    <div>
      <p class="eyebrow">Decision</p>
      <h2>Gate the subscription first</h2>
    </div>
    <p class="section-meta">FE impact analysis</p>
  </div>
</section>
```

Use a lead paragraph when the opening needs a compact thesis:

```html
<p class="lede">The decision and the conditions that could change it.</p>
```

## Prose and composition

Use `.prose` for spaced paragraphs, `.columns` for long parallel prose, and grids only when the content genuinely has parallel structure:

```html
<div class="grid two">...</div>
<div class="grid three">...</div>
<div class="grid sidebar">...</div>
<div class="prose">...</div>
<div class="columns">...</div>
```

Keep sequential arguments in normal document flow. A two-column grid is useful for alternatives or text beside code; it is weaker for a single continuous explanation.

For an implementation sequence, use the supported timeline component. Each item is a compact, numbered card; do not compose a sequence from unstyled spans and loose paragraphs.

```html
<div class="timeline">
  <div class="timeline-item">
    <span class="timeline-index">1</span>
    <div><h3>Align the contract</h3><p>Confirm the data and migration boundary.</p></div>
  </div>
</div>
```

Use only the shared component classes in this guide. If a new visual form is needed, add it to the shared stylesheet and document it here before generating documents with it.

Preserve rhythm: each visual component needs clear space before the next one. Prefer the section’s built-in flow gap and a component’s internal spacing over ad-hoc margin overrides.

## Decisions and supporting facts

Use restrained framing:

```html
<div class="verdict">
  <h3>Recommendation</h3>
  <p>Decision, scope, and strongest condition that could reverse it.</p>
</div>

<div class="callout">A caveat or operational implication.</div>
<div class="panel">A compact supporting group.</div>
```

Use metrics for two to four headline values:

```html
<div class="metrics">
  <div class="metric"><span>Monthly cost</span><strong class="accent">$247</strong></div>
  <div class="metric"><span>Active agents</span><strong>100</strong></div>
</div>
```

## Tables

Wrap tables for narrow screens. Keep prose outside the table when it explains the significance of several rows.

```html
<div class="table-wrap">
  <table>
    <thead><tr><th>Option</th><th class="numeric">Cost</th><th>Tradeoff</th></tr></thead>
    <tbody>
      <tr><td class="emphasis">Cloud</td><td class="numeric">$247</td><td>Managed operations</td></tr>
      <tr><td class="recommend">Recommended</td><td class="numeric">...</td><td>...</td></tr>
    </tbody>
  </table>
</div>
```

Use tables selectively. One good comparison table plus explanatory sections is usually stronger than several repetitive matrices.

## Code

Use inline `<code>` only for short identifiers, routes, and values; the shared stylesheet renders it as a GitHub/T3Code-style subtle rounded token with no heavy border. Set the real language in a fenced block’s class. The runtime adds highlighting and a copy button.

```html
<div>
  <div class="code-caption"><h3>Cost model</h3><p>TypeScript</p></div>
  <pre><code class="language-typescript">const total = base + usage;</code></pre>
</div>
```

Escape `<`, `>`, and `&` inside code. Explain what the code proves and what it cannot prove.

## Mermaid

Use Mermaid when relationships are harder to understand linearly. The runtime supplies pan, zoom, 1:1 reset, and fullscreen viewing.

```html
<figure class="diagram">
  <figcaption><strong>Request path</strong><span>Pan, zoom, or open fullscreen</span></figcaption>
  <pre class="mermaid">flowchart LR
    A[Agent] --> B[Preview service]
    B --> C[Private URL]</pre>
</figure>
```

Keep node labels short. Explain the implication in nearby prose instead of turning the diagram into a wall of text.

## Charts

Use inline SVG for a small, deterministic line or bar chart. Include a meaningful `role="img"` and `aria-label`, label axes directly, and put exact values in text or a nearby table. Keep chart colors anchored to CSS variables such as `var(--pink)`, `var(--ink)`, and `var(--muted)`.

## Sources and uncertainty

Place source links at the end or beside the claims they support:

```html
<ul class="sources">
  <li><a href="https://example.com" target="_blank" rel="noreferrer">Descriptive source title</a></li>
</ul>
```

Use `<p class="note">` for model assumptions, exclusions, dates, and uncertainty. Distinguish official prices from modeled costs. Never manufacture a citation to make the document look complete.

## Accessibility and resilience

- Keep heading order logical.
- Give links descriptive text.
- Add captions or accessible labels to tables and charts.
- Retain visible prose for the central conclusion; interactive content is supporting material.
- Keep essential meaning available if Mermaid, the webfont, or syntax highlighting cannot load.
- Check narrow layouts for horizontal overflow except inside intentional table and code scrollers.
