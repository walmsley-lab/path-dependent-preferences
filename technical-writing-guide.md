# Approachable Technical Writing Guide

## Purpose and use

Write technical findings with research-paper rigor and excellent-blog clarity, primarily for ML, AI, software, systems, and hardware. A curious reader should understand the question, result, and limits; a specialist should be able to audit the work.

**Make the real complexity understandable; do not make the work merely sound simple.**

Start with Section 6, write and revise with Part I, then audit with Sections 7–10. Venue rules override formatting and register, never evidence. Apply Appendix A only when no venue template governs production.

| Output | Apply |
| --- | --- |
| Paper or preprint | Entire guide; venue template; formal references |
| Technical report or note | Entire guide; Appendix A unless another template applies |
| Research post | Sections 1–7 and 9–10; relevant Section 8 modules; inline links may replace formal references |
| Computational notebook | Entire guide, including the notebook module; Appendix A only for published exports |

# Part I: Write the piece

## 1. Give readers a clear way in

Write for three depths:

1. **Curious:** why the question matters and what was found.
2. **Technical:** how the design supports the finding.
3. **Specialist:** assumptions, settings, and artifacts needed to inspect or repeat it.

Use a specific, searchable title. Give abstracts five moves: problem, gap, approach, result, and bounded implication. **Report the result; do not merely promise it.** Open posts with the question, surprise, or result. By the end of either opening, readers should know the subject, contribution, and scope.

Organize around findings, not project chronology. Adapt structure to the contribution; theory, systems, and empirical work need different outlines. Keep the main text sufficient to defend every central claim. Put exhaustive settings, derivations, and secondary analyses in appendices or artifacts.

Organize related work by idea or methodological difference, not as a paper-by-paper catalogue. Compare against the strongest relevant work and state the distinction precisely.

Use contribution lists only when they improve scanning, and omit routine roadmap paragraphs.

Let the conclusion state what the evidence supports, what remains unresolved, and the most useful next step without introducing new claims.

### Length and paragraphs

Without a limit, plan roughly 2,000–4,000 main-text words for a note, 4,000–7,000 for a paper, and 150–250 for an abstract. Unless a venue says otherwise, main-text counts exclude references, acknowledgments, availability statements, and appendices. Cut repeated motivation, literature catalogues, throat-clearing, decoration, and duplication before evidence, negative results, limitations, or reproducibility details.

Under a hard limit, keep each central claim’s result, comparison, uncertainty, and principal limitation. Move settings, derivations, full ablations, and secondary analyses, citing their location. If a claim cannot fit with its limits, drop the claim rather than thin its evidence.

Give each paragraph one job and reveal it early. Split when the subject, evidentiary role, time frame, or abstraction changes. Most paragraphs fall near 60–150 words; treat 180 words as an inspection prompt, not a violation.

## 2. Keep claims inside the evidence

Signal each statement’s status:

- **Observation:** “Latency decreased from X to Y under workload Z.”
- **Interpretation:** “This pattern is consistent with…”
- **Possible mechanism:** “One explanation is…”
- **Hypothesis:** “We hypothesize that…”
- **Implication:** “If this generalizes, it may…”
- **Unknown:** “This experiment cannot distinguish…”

Repair three common failures:

- **Anthropomorphism:** Replace unsupported claims that a model *understands, knows,* or *reasons* with measured behavior. *Learns* is acceptable for an explicit optimization process, not as evidence of human-like comprehension.
- **Overclaiming:** Use *proves, causes, robust,* or *generalizes* only when the design supports that meaning. Otherwise name the evaluated conditions.
- **Evasive hedging:** A qualifier should identify a locatable uncertainty, such as a small sample or untested mechanism. Avoid stacked hedges such as *may possibly suggest*. Hedge once and say what would remove it.

Analogies can explain, but they are not evidence. State where they stop matching. Distinguish measurements from simulations, estimates, projections, and illustrations.

Report nulls, failures, exclusions, anomalous runs, device yield, and material deviations. Label exploratory and post hoc analyses.

## 3. Write plainly, precisely, and like a person

Prefer concrete nouns, active verbs, and the shortest wording that preserves meaning. Keep actors and conditions visible. Define necessary jargon and abbreviations, then use them consistently. Give the result before a long derivation when that will not mislead.

Replace vague modifiers with measurements or criteria. Reserve *statistically significant* for a defined test and pair it with effect magnitude and uncertainty. Do not report more digits than the evidence supports. Round consistently and distinguish percent from percentage points: 40% to 50% is 10 percentage points or 25% relative.

Warmth, first person, contractions, and restrained humor are welcome when appropriate. Let personality come from curiosity, lucid analogies, candid limits, and surprising observations, not inflated claims.

Avoid em dashes. Prefer a period, comma, colon, semicolon, or parentheses according to the relationship. This is a house-voice choice, not evidence of authorship or writing quality; quoted material is exempt.

**Be playful about the research experience, never about the precision of the evidence.**

## 4. Match form to task

| Reader’s task | Form |
| --- | --- |
| Follow an argument or qualification | Prose |
| Scan parallel items | Bullets |
| Follow ordered steps | Numbered list |
| Retrieve exact values | Table |
| See trends, distributions, or relationships | Data figure |
| Understand structure, flow, timing, or layout | Diagram |
| Inspect a formal relationship | Equation |
| Reproduce an implementation detail | Code |

Tables need not fill the page. Left-align text and right-align numeric columns; align comparable decimals when practical. Align headers with their columns. Bold headers are optional; hierarchy and alignment matter more. Do not use bold to imply meaningful superiority when differences fall within reported uncertainty, and define any emphasis rule in the caption. Distinguish zero, missing, unmeasured, and inapplicable values. Avoid decorative rules and provide machine-readable data when practical.

Number tables and figures in first-mention order and give each a self-contained caption. Put table titles above and figure captions below unless a venue requires otherwise. Each figure should answer one question, and its caption should state the principal answer rather than merely describe the contents. Keep captions focused on the question, result, conditions, and essential uncertainty; move extended methods and interpretation into the body. Label axes, units, samples, uncertainty, aggregation, and logarithmic scales; name log scales in the prose that interprets them. Disclose altered axes, smoothing, filtering, normalization, and omissions. Use readable sizing, alt text, and underlying data. Never encode meaning by color alone: add labels, markers, patterns, or line styles and verify grayscale. Summarize the key comparison in prose for accessibility.

For AI figures, show individual runs or uncertainty bands, not only the best seed; state smoothing and checkpoint-selection rules. Label benchmark bars with values and uncertainty; avoid truncated axes. Give confusion-matrix counts and normalization. Treat embeddings and generated examples as diagnostic views. Do not present attention or saliency as explanation without validation ([Jain and Wallace, 2019](https://aclanthology.org/N19-1357/); [Adebayo et al., 2018](https://papers.nips.cc/paper/8160-sanity-checks-for-saliency-maps)). For attention or saliency views, identify the method, layer or component, input, and question being investigated. Report projection and example-selection methods; include representative, random, and failure cases. Use perceptually ordered heatmaps.

### Make mathematics readable

Present each important equation at three levels:

1. **Purpose:** Before the equation, say what it computes, models, or establishes and why the reader needs it.
2. **Notation:** Define every symbol near its first main-text use. State whether it is a scalar, vector, matrix, tensor, set, or function; give shapes, units, domains, index ranges, and assumptions when relevant. For tensors, name the dimension order.
3. **Interpretation:** After the equation, read it in ordinary language. Explain what each major term contributes and what changes when an input or parameter increases, decreases, or reaches an edge case.

Keep short equations inline and display long or important ones. Use consistent notation and do not reuse a symbol for different concepts. When symbols recur across sections, provide a notation table with **Symbol**, **Meaning**, and **Shape or units**; still define symbols locally. Add a small worked or dimensional example when the operation remains abstract. Punctuate equations as sentences and number only equations cited later. Use semantic LaTeX or MathML rather than equation screenshots; if an image is unavoidable, provide alt text that reads the notation aloud. Do not include equations merely to signal rigor or call notation “obvious.”

### Make code auditable

Introduce each code sample with what it demonstrates and why it is present. Distinguish executable code from pseudocode. State the language and version, inputs, dependencies, assumptions, and expected output. Code supporting a central claim should run as shown or link to the exact archived implementation; label omitted setup or boilerplate. Put full implementations and tests in artifacts. Do not use screenshots of code or expose credentials, private data, or machine-specific paths.

## 5. Revise in passes

Do not polish sentences before the argument works.

1. **Structure:** align the question, contribution, claim order, sections, title, opening, and conclusion.
2. **Evidence:** put a result, comparison, uncertainty, and limitation behind each claim.
3. **Outside test:** while restructuring is cheap, ask a non-specialist to state the question, finding, and largest limitation.
4. **Clarity:** remove noun stacks, vague modifiers, buried subjects, and unnecessary jargon.
5. **Compression:** try cutting 10% without losing evidence or qualifications.
6. **Sound:** read aloud and repair sentences that fail once.
7. **Verification:** run Section 10, then recheck numbers, citations, links, and artifacts.

During the structure pass, read only the title and headings as an outline. Each should be specific, concise, parallel with its peers, and faithful to the section it introduces. Remove headings that merely repeat the title, promise more than the section supports, or divide prose without improving navigation. Check the rendered document for stranded headings and unclear hierarchy.

# Part II: Plan and audit the reporting

## 6. Define the work

Record the contribution type, readers, output and venue, intended reproducibility level, relevant human-data, safety, environmental, and dual-use concerns, contributors, funding, support, and conflicts. For AI-assisted drafting, stop and ask when missing information could change a claim, comparison, or format decision. Otherwise proceed and flag the gap explicitly rather than guessing.

## 7. Audit claims and reproducibility

For each important claim, ask:

- What evidence supports it?
- What control, baseline, specification, or counterfactual makes it meaningful?
- What alternatives remain?
- What uncertainty arises from sampling, measurement, implementation, or analysis?
- Where might it fail?

Report uncertainty beside the result. Define the quantity, units, sample size, aggregation, variation, and method. For inference, report the estimand or hypothesis, test or model, effect size, interval, assumptions, and multiplicity treatment. Do not replace magnitude and uncertainty with a thresholded *p*-value. Label confirmatory, exploratory, and post hoc analyses; preregister when appropriate.

State the level supported:

1. **Repeatability:** same team and conditions.
2. **Artifact reproducibility:** another team uses the authors’ artifacts.
3. **Independent replication:** another team uses an independent implementation or apparatus.
4. **Generalization:** the finding persists under meaningfully different conditions.

Venue terminology varies; use its mapping and state how it corresponds to these concepts.

## 8. Apply relevant reporting modules

### Machine learning and AI

- **Data:** provenance, license, consent, processing, exclusions, splits, contamination, and test exposure, including repeated benchmark peeking.
- **Model:** architecture, parameters, version, dependencies, prompts, training, hyperparameters, selection, seeds, and run count.
- **Evaluation:** baselines, parity, ablations, sensitivity, negative results, uncertainty, limits, and affected populations.
- **Model grading:** judge and version, rubric, prompt, settings, order controls, sensitivity, and human agreement. **Model judgments are not ground truth.**
- **Resources:** compute, hardware, runtime, energy and cost boundaries, privacy, labor, misuse, safeguards, and artifacts.

Use model cards or datasheets when they add information, not as empty compliance artifacts.

### Software and systems

Report intended use, architecture, interfaces, security assumptions, unsupported cases, and defects. Provide versioned source, dependencies, configuration, build and test instructions, workloads, benchmark procedure, repetitions, distributions, parity, limits, and resource use. Cite the archived release.

### Hardware and physical experiments

Provide schematics, bill of materials, revisions, firmware and toolchain, fabrication, tolerances, and conditions. Report samples, yield, failures, variation, controls, safety, calibration and traceability, resolution, drift, and environment. Separate measurement from simulation; provide data, analysis code, uncertainty, and repeatability evidence.

### Computational notebooks

Treat notebooks as executable narratives or controlled job interfaces, not records of an undocumented live session. A notebook must run top to bottom from a clean kernel, expose parameters, pin its environment and data versions, avoid hidden state and secrets, and reproduce reported outputs. Move reusable logic into tested modules. If a notebook runs in production, parameterize, version, test, monitor, and schedule it like any other production job.

### Other contributions

- **Theory and algorithms:** assumptions, definitions, guarantees, proof status, counterexamples, complexity, and empirical connection.
- **Datasets and benchmarks:** provenance, consent and labor, annotation, splits, contamination, uses, licenses, maintenance, and gaming risks.
- **Replications:** original claim, fidelity, deviations, success criteria, and artifact independence.
- **Syntheses:** search, screening, inclusion, extraction, quality, and heterogeneous evidence; use PRISMA when applicable.

**A polished demonstration, screenshot, dashboard, or notebook is not evidence by itself.**

## 9. Cite, disclose, and package

Cite primary evidence near the claim; distinguish prior work and cite exact datasets, archived releases, and preprint versions. Provide availability statements, stable identifiers, licenses, and restrictions. For posts, use versioned or archived links for evidence essential to a claim. Follow double-blind rules.

Package artifacts with a README covering environment, setup, reproduction, expected outputs, licenses, and limitations. Record roles, funding, conflicts, versions, and corrections.

AI must not invent, overstate, erase contradictions, or infer undocumented choices. Preserve values, units, uncertainty, qualifiers, and citation scope; verify AI-added facts, calculations, quotations, and citations. Humans remain responsible. Follow venue policy; otherwise disclose material AI involvement, its contribution, and verification.

## 10. Final audit

- Can a non-specialist state the question, finding, and limitation?
- Do the title, opening, body, and conclusion state the same bounded contribution?
- Do the title and headings form a concise, accurate outline with consistent hierarchy and no stranded headings?
- Does each claim have evidence, a fair comparison, uncertainty, and appropriate scope?
- Are observation, interpretation, mechanism, hypothesis, implication, and unknown distinct?
- Do methods and artifacts support the claimed reproducibility level?
- Are relevant ethics, safety, misuse, environmental, and human-data issues addressed?
- Does each use of prose, lists, tables, figures, diagrams, equations, code, or notebooks serve a distinct task?
- Can a reader find every symbol’s meaning, shape or units, and a plain-language interpretation of each important equation?
- Can a reader identify what central code demonstrates, its environment and inputs, and the output it should reproduce?
- Are figures legible at normal size, in grayscale, and without color-dependent meaning?
- Are citations, artifacts, versions, licenses, roles, funding, conflicts, and AI use verified?
- Do humor and analogy clarify rather than exaggerate?

## Writing exemplars

Study these for their structure, pacing, and integration of evidence, not as templates to copy.

- Thinking Machines Lab, [*LoRA Without Regret*](https://thinkingmachines.ai/blog/lora/) (2025): layers intuition, experiments, and caveats without losing momentum.
- Olah, Mordvintsev, and Schubert, [*Feature Visualization*](https://distill.pub/2017/feature-visualization/) (2017): integrates argument, interactive visuals, methods, and uncertainty.
- Anthropic, [*Tracing the Thoughts of a Large Language Model*](https://www.anthropic.com/research/tracing-thoughts-language-model) (2025): makes a complex method legible while separating observations from interpretation.
- 3Blue1Brown, [*But What Is a Neural Network?*](https://www.3blue1brown.com/lessons/neural-networks/) (video, 2017): models pacing and lets visuals carry spatial relationships.

# Appendix A: Field Note Production Style

This appendix controls the appearance and export of independent technical notes. A venue template overrides it. The default is compatible with arXiv’s requirements: single-spaced text, 10–14 point type, margins of at least one inch, and no margin notes. Archive builds use standard TeX fonts or repository-vendored font files; system-installed fonts belong only in local or editorial builds. Produce a separate editorial edition only when it serves a real reading need. Implement this appendix through a tested, version-controlled template; the prose defines outcomes rather than engine-specific commands.

## A.1. Page and type

| Role | Default |
| --- | --- |
| Body | Inconsolata, or Latin Modern Mono for portable archives; 12 pt, single spaced, ragged right |
| Page | Screen-first: 1.2-inch side and bottom margins; 1-inch top margin |
| Measure | 60–75 characters per line, including spaces |
| Title | TeX Gyre Heros, 20–24 pt, semibold |
| Subtitle | 11–13 pt, regular |
| Author | 10–11 pt, regular |
| Date, version, or status | 9–10 pt, regular; omit when the venue does |
| Section | 14–16 pt, semibold, sentence case |
| Subsection | 11–12 pt, semibold, sentence case |
| Run-in | Body-size bold; one paragraph only |
| Caption | 8–9 pt |

At 12 pt, Inconsolata yields about 73 characters across this Letter-size text block and about 70 on A4. Treat 75 as a ceiling; adjust the measure when the font changes. Use fixed symmetric margins for screen-first PDFs. Mirror inner and outer margins only for a bound duplex edition, and label that build separately. Do not place content in the margin.

Center the title block for conventional academic papers. Keep the author near body size and the date, version, or status smaller so metadata remains subordinate to the title and subtitle. A left-aligned title block is acceptable for an editorial note, but align the entire block consistently rather than mixing conventions.

For a licensed editorial edition, Cartograph CF may replace Inconsolata and Articulat CF may replace TeX Gyre Heros. Monospaced body text is a deliberate house voice, but it can reduce reading speed. Test long documents with representative readers; use a proportional text face if fatigue outweighs identity.

Use a compatible math face and genuine bold and italics. Use bold for hierarchy or result labels, italics for titles, terms, and restrained emphasis, and underlining only for digital links. Reserve capitals for acronyms and short labels. Use no more than three heading levels. In print, identify links through wording or references.

Treat the abstract as a standfirst: label it **Abstract** at the left and set it in a slightly narrower measure than the body. Match the label's type size, weight, and post-heading spacing to subsection headings; let numbering, position, and measure distinguish its role. Reserve a separate title page for long or institutional reports.

## A.2. Color

Use the **Field Note** palette semantically, not decoratively:

| Role | Color |
| --- | --- |
| Text | Carbon `#202428` |
| Digital paper | Warm Ivory `#F7F3E8` |
| Links and references | Bay `#315B6B` |
| Key result | Bridge `#A9422C` |
| Secondary result or caveat | Sage `#616E5A` |

Keep body text Carbon and print backgrounds white. Carbon on Warm Ivory exceeds WCAG AA contrast for ordinary text. Use one accent in prose and at most three hues per figure unless the data requires more. Never encode meaning by color alone: add direct labels, markers, patterns, or line styles. Verify grayscale and color-vision accessibility. Use pale tints only across large areas, not for small text.

## A.3. Tables, figures, equations, and code

Apply Section 4. Style tables with sparse horizontal rules and no vertical grid unless grouping requires it. Headers may be semibold; keep alignment consistent with the column. Do not force a table or figure to full width when a narrower measure improves comparison.

Number equations only when referenced later, sequentially through the document unless a venue numbers by section, and place numbers at the right margin. Use inline code for file names, versions, commands, and short identifiers. Use fenced blocks for multiline code and preserve syntax highlighting only when it remains legible in grayscale.

Export plots as PDF or SVG when possible. Reserve raster formats for photographs or inherently raster data, use adequate resolution, and do not rasterize text unnecessarily.

## A.4. Pagination and export

Use page numbers throughout. Independent notes of roughly eight pages or more should place a concise running title on pages after the first. For versioned drafts or preprints, place a compact status such as `Preprint · v0.1` at the opposite edge. Repeat the author only when a venue or collection needs it. Use `N / M` or `Page N of M` when pages may be printed or separated. Do not repeat a long subtitle in the header. Venue templates override these rules.

State publication status with a fixed version and date. Use `Working draft` for private circulation and `Preprint` for an unpublished public release. After arXiv assigns an identifier, prefer `arXiv:YYMM.NNNNN · vN`. Maintain a separate anonymous build for double-blind review. An accepted manuscript may name the venue when its policy permits; a published version should remove the preprint label and use the final citation and DOI. Update the arXiv journal reference and DOI after publication.

Keep headings with their opening paragraph and captions with their objects. Paragraphs may span pages, but do not strand a single opening or final line, especially a very short line. Use widow and orphan controls before inserting manual page breaks. Do not let a float interrupt a sentence, and avoid premature manual breaks. Do not leave a nearly empty final page because of a forced break or one stranded reference; first adjust ancillary spacing or bibliography type, not the body text.

Build PDF from semantic source. Generate EPUB or HTML when reflow, accessibility, or mobile reading matters; do not convert from the PDF. Use a fixed publication date and version for archived releases rather than dynamic build values. Verify heading navigation, MathML, tables, cross-references, link behavior, alt text, and code overflow separately in every format.

## A.5. Production audit

- Does the document follow the venue before the house style?
- Are type, spacing, margins, headings, and links consistent?
- Do tables and figures remain clear in grayscale and at normal reading size?
- Is every color distinction duplicated by a non-color cue?
- Are captions attached, cross-references correct, and alt text present?
- Does each exported format preserve navigation, equations, tables, and code?
- Does the archived release record a fixed date and version?
- Can a detached page be identified and returned to the correct document and page order?
- Is the draft, preprint, review, accepted, or published status current and appropriate for this build?
- For any artifact bundle containing an `.ipynb` file, does the notebook run from a clean kernel with exposed parameters, pinned versions, and reproduced outputs?
- Are all fonts licensed, embedded when permitted, and available to the build?

## Sources

- **Writing and structure:** Gallagher, [*Software Technical Writing*](https://jamesg.blog/book.pdf) (2024); Widom, [*Tips for Writing Technical Papers*](https://cs.stanford.edu/people/widom/paper-writing.html) (2006).
- **Research reporting:** APA, [JARS](https://apastyle.apa.org/jars) and [tables and figures](https://apastyle.apa.org/style-grammar-guidelines/tables-figures); [Nature Portfolio standards](https://www.nature.com/nature-portfolio/editorial-policies/reporting-standards); [NeurIPS paper checklist](https://neurips.cc/public/guides/PaperChecklist).
- **Quantitative evidence:** Taylor and Kuyatt, [NIST TN 1297](https://doi.org/10.6028/NIST.tn.1297) (1994); Wasserstein and Lazar, [ASA statement on *p*-values](https://doi.org/10.1080/00031305.2016.1154108) (2016).
- **Reproducibility and attribution:** ACM, [artifact review](https://www.acm.org/publications/artifacts) and [badging terminology](https://www.acm.org/publications/badging-terms); NISO, [CRediT taxonomy](https://credit.niso.org/) (2022).
- **ML documentation and evaluation:** Mitchell et al., [*Model Cards for Model Reporting*](https://doi.org/10.1145/3287560.3287596) (2019); Gebru et al., [*Datasheets for Datasets*](https://doi.org/10.1145/3458723) (2021); Zheng et al., [*Judging LLM-as-a-Judge*](https://papers.nips.cc/paper_files/paper/2023/hash/91f18a1287b398d378ef22505bf41832-Abstract-Datasets_and_Benchmarks.html) (2023).
- **Interpretability views:** Jain and Wallace, [*Attention Is Not Explanation*](https://aclanthology.org/N19-1357/) (2019); Adebayo et al., [*Sanity Checks for Saliency Maps*](https://papers.nips.cc/paper/8160-sanity-checks-for-saliency-maps) (2018).
- **Accessibility:** W3C, [use of color](https://www.w3.org/WAI/WCAG21/Understanding/use-of-color.html), [non-text contrast](https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html), and [text contrast](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html).
- **Research syntheses:** Page et al., [PRISMA 2020](https://doi.org/10.1136/bmj.n71) (2021).
- **Computational notebooks:** [Project Jupyter documentation](https://docs.jupyter.org/); Google Cloud, [notebook practices](https://cloud.google.com/blog/products/ai-machine-learning/best-practices-that-can-improve-the-life-of-any-developer-using-jupyter-notebooks).
- **Mathematical writing and accessibility:** Knuth, Larrabee, and Roberts, [*Mathematical Writing*](https://www-cs-faculty.stanford.edu/~knuth/papers/cs1193.pdf) (Stanford Computer Science Report 1193, 1988); AMS, EMS, LMS, and SIAM, [accessible mathematics](https://epubs.siam.org/pb-assets/author_guidelines_accessible_mathematics.pdf).
- **Venue and production:** arXiv, [format requirements](https://info.arxiv.org/help/policies/format_requirements.html) and [TeX submissions](https://info.arxiv.org/help/submit_tex.html); [Tufte-LaTeX](https://mirrors.ctan.org/macros/latex/contrib/tufte-latex/sample-book.pdf); Nielsen Norman Group, [how people read online](https://www.nngroup.com/articles/how-people-read-online/).