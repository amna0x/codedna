# CodeDNA website blueprint

Implementation brief for the website builder. Updated 27 October 2026.
Use this together with PROJECT_SPEC.md, ARCHITECTURE.md and the current
BLUEPRINT_COMPLETION.md. Build the website around verified functionality.
The website is the public product/distribution surface; the analysis runs locally.

## 1. Product and audience

CodeDNA is a local software-engineering platform for understanding changes and
choosing regression tests. It has a Python core, Java/Python language plugins,
a Theia/Electron desktop IDE, CLI, loopback API and MCP tools for coding agents.

Primary users: students/developers maintaining tested projects; Java teams with
slow regression suites; developers using coding agents; FYP examiners evaluating
the method and evidence. Give beginners a clear desktop route and experienced
users precise CLI/plugin information.

Primary action: get the desktop app, open a repository, inspect changes, review
recommended tests, then explicitly consent to execution. Secondary actions:
browse languages, read setup/limitations, inspect research and reproduce a result.
The website must not imply that pasting a repository URL will analyse it online.

Suggested hero copy:

> See what your change affects. Run the tests your evidence supports.

Supporting copy: CodeDNA maps Java and Python changes to affected code and tests.
Validated risk stopping is currently Java-specific; unsupported or inadequate
evidence means the full suite. Analysis stays on your machine.

Do not advertise guaranteed bug detection, universally faster CI, a model that
transfers to every project, a first-ever conformal selector, or an AI agent that
has been shown to write better patches. Those claims are not established.

## 2. Current capabilities and exact limits

| Capability | Java | Python/mixed | Website wording |
|---|---|---|---|
| Git changes / WORKTREE | Implemented | Implemented | Inspect committed and uncommitted changes |
| Declaration mapping | Tree-sitter Java | Python AST | Changed declarations with source locations |
| Dependency graph | Typed/labelled type relationships | Imports/inheritance and module/class relationships | Confirmed, heuristic and unresolved evidence stay distinct |
| Test discovery | JUnit and Maven/Gradle layouts | Static pytest module discovery | Discovered tests, with known framework/build limits |
| Execution | Opt-in Maven/Gradle | Opt-in pytest, mixed dispatch | Runs project code only with consent |
| Risk stopping | B10 default; CRC opt-in | No validated model; full-suite fallback | Evidence-based stopping where supported |
| History/replay | Implemented | Shared recording/execution where supported | Project-local outcomes and saved research replay |
| Agent brake | Implemented | Conservative full-suite plan/execution | Required tests and actual passed/blocked/incomplete verdicts |
| Language distribution | Java/Python bundled | Same | Optional downloads require a real published release |

Ant/TestNG and dynamic pytest collection are not broadly supported. There are no
cross-language dependency edges. Java risk evidence does not automatically apply
to Python, JS/TS or Go. The model uses 15 live features; retrospective studies
also used a 19-feature setup. Explain that difference on Research/Limitations.

## 3. Navigation and page map

Top navigation: Product, Language plugins, Docs, Research, Downloads.
Persistent logo returns home. Footer: About/FYP, Changelog, Privacy/local data,
Licence, Source access, report/evidence links. Avoid accounts, payments, plugin
ratings and third-party submissions: these are outside the project scope.

| Route | Purpose | Primary action |
|---|---|---|
| / or index.html | Clear value and credible demonstration | Get CodeDNA |
| /product | Detailed workflow and screenshots | Follow quick start |
| /plugins or plugins.html | Language capability cards and acquisition | Get bundled app / official optional release |
| /plugins/<id> | Optional detail page once the catalogue grows | Review exact version and requirements |
| /downloads or downloads.html | Desktop version/platform/checksum/status | Download a published installer |
| /docs | Searchable guide index | Choose desktop / CLI / agents |
| /docs/quick-start | First real repository walkthrough | Complete a safe first analysis |
| /docs/agents | MCP setup, consent and verdicts | Configure the brake |
| /research | Question, methods, results, limits and artifacts | Inspect evidence |
| /changelog | Release changes and migration notes | Pick a supported version |
| /about | FYP scope, team and attribution | Understand project context |

The current repository uses static HTML pages. Keep the first release static;
framework migration is optional and must preserve catalogue URLs and links.

## 4. Homepage, section by section

1. **Hero:** one headline, the supporting copy above, Get CodeDNA and View
   workflow. Include a real current IDE image or labelled illustrative mockup.
   If no public installer exists, say Release download not published and link
   to availability/developer setup. Never make a dead Download button.
2. **Three-step workflow:** compare a change; inspect affected code/tests;
   run recommended tests with consent. A fourth small note explains full-suite
   fallback when history does not justify skipping.
3. **Interactive example:** a small static graph from change to dependent code
   to tests. Clicking a node shows an explanation path. Label Example data.
   It is an illustration, not an upload/online-analysis endpoint.
4. **Feature grid:** change mapping, impact graph, test selection, checked risk
   stopping, project history, agent brake. Link each to its documentation.
5. **The brake story:** a failing required test blocks completion; missing or
   skipped required tests remain incomplete. A passed check is not proof the
   patch has no bugs. Show all states rather than a single green approval card.
6. **Languages:** Java and Python marked Available/bundled. JS/TS can be Planned,
   Go Under consideration. Do not show Install for an unimplemented language.
7. **Research summary:** one plain statement of the question and link to the
   full results. Present uncertainty and costs with any percentages.
8. **Final action:** desktop availability, requirements and quick-start link.

Keep technical implementation details on Docs/Research, not in the beginner's
main path. Avoid long library lists in the hero.

## 5. Language plugin catalogue and acquisition

The single source is website/catalogue/index.json. The core's catalogue parser
and plugin manager already enforce pinned versions, SHA-256, compatibility and
an official release location. The website displays the same data; it must not
maintain a second hand-edited catalogue with different versions.

A card shows language name, bundled/optional/planned state, short capability
summary, supported test/build tools, current version, plugin API requirement,
licence, source access, and known limits. Put 'risk selection supported' and
'structural analysis only / full-suite risk fallback' in explicit text.

### Bundled Java/Python flow

- State Included with CodeDNA and already available in the desktop bundle.
- Primary link: Get CodeDNA with this language, leading to Downloads.
- In-app instruction: Extensions → Language plugins, Ctrl+Shift+X.
- Do not ask users to download/install the same bundled version again.
- Source collaborators can use the repository setup guide; the source is private.

### Optional published plugin flow

1. User reviews language, exact version, plugin API and prerequisites.
2. Website offers only the catalogue's verified official wheel URL.
3. Show the complete SHA-256, not just a shortened decorative fingerprint.
4. Provide a copyable pinned command such as `codedna plugins install ID VERSION
   --yes`, with an explanation that the user should review it before running.
5. Explain that the download does not install itself. In the app, installation
   requires a separate review/confirmation; core verifies the checksum.
6. After installation, show restart requirements and a way to inspect the loaded
   version. Preserve the previous working plugin on failed updates.

Never accept an arbitrary install URL from a text box. Do not make the website
silently call the user's loopback API, obtain its token, or execute local commands.
A custom app-opening URI must not be advertised until an actual protocol handler
exists and is tested; currently the user opens the app normally.

### Required states

Loading; catalogue offline; invalid catalogue; bundled; available optional
release; incompatible API; no published release; install confirmation/cancel;
download failed; checksum mismatch; dependency refusal; restart required;
installed version; update available; update rollback; removal refused for bundled
languages. Installed languages must remain usable while the catalogue is offline.

The website acquisition UI is now implemented in plugins.js, with tests for its
bundled/optional/offline states and refusal of invalid official-download metadata.
Actual Java/Python catalogue entries remain bundled and have no download URLs.

## 6. In-app Extensions experience

Use a permanent activity-bar Extensions icon. Its container contains Language
plugins. Restore it for existing as well as fresh workspace layouts; do not
steal focus from the editor on startup. Ctrl+Shift+X and a command-palette entry
open it. The UI is implemented through extensions-widget-factory.ts and the
existing PluginsViewWidget, not a second installer or marketplace.

Top section: installed Java/Python immediately, names/versions/API and load
problems. Second section: official catalogue and any compatible optional
versions. Loading the online catalogue must not hide the installed languages.
Explain that analysis plugins differ from editor completion/debugging extensions.
Do not list an editor VSIX as if it supplied CodeDNA's dependency/risk analysis.

## 7. Desktop Downloads page

Each published release needs: version, release date, OS/architecture, size,
full installer SHA-256, signing status, release notes, prerequisites, known
limitations and previous-version access. Keep real release metadata in a file
or generated release manifest, not scattered through page components.

Current desktop: Windows x64 prototype. The installer bundles the analysis
Python/ML/API runtime and both language plugins. It does not supply every
project's JDK/build system or pytest dependencies. It is unsigned. Clean-PC
installation is still awaiting an external test; say so until evidence exists.
Do not add Mac/Linux installer buttons until those builds exist and are tested.

Use a separate 'Build from source' route for collaborators. Do not imply a private
GitHub clone works for everyone. The current downloads.html records unpublished
status; a local installer is not automatically a public release.

## 8. Hosting and release pipeline

Do not make the private source repository public merely to host the website.
Recommended arrangement: static site hosting plus a dedicated owner-controlled
public release destination for approved binaries/wheels. Licence and publication
scope must be decided before public artifacts are uploaded.

Current constants:

- Core catalogue URL: `https://mohibk0004-del.github.io/codedna/catalogue/index.json`.
- Allowed wheel prefix: `https://github.com/mohibk0004-del/codedna/releases/download/`.

These presently refer to the private source project. A separate public release
repository/domain needs a deliberate coordinated update to
`backend/codedna/plugins/manager.py:OFFICIAL_CATALOGUE` and
`backend/codedna/plugins/catalogue.py:OFFICIAL_RELEASES`, the website validation,
tests and documentation. Do not silently loosen the checks to any URL.

Release order:

1. Choose the actual public destination and licence, retaining source privacy.
2. Freeze code/plugin versions and build verified installer/wheels.
3. Test compatibility, dependency behavior, cancellation, update/rollback and
   installation in the actual frozen desktop, not just a source environment.
   The current manager's pip backend uses its Python environment; arbitrary
   wheel installation in a frozen desktop must be verified/fixed before being
   advertised. Bundled Java/Python do not require that path.
4. Perform the clean-PC test using CLEAN_PC_ACCEPTANCE.md.
5. Upload only approved artifacts; compute hashes from the uploaded exact bytes.
6. Verify anonymous downloads from a signed-out browser.
7. Publish the catalogue last, after all referenced artifacts exist.
8. Deploy the static site and run navigation/catalogue/download smoke checks.
9. Verify the app reads the same catalogue and handles the site being offline.

No public upload, repository visibility change or release publication is performed
by this blueprint. Current download availability is deliberately honest.

## 9. Documentation content

Provide desktop and CLI tracks. Quick start covers opening a Git folder,
BASE/HEAD versus WORKTREE, reading changed declarations, confirmed/heuristic
edges, test recommendations, explicit run consent, actual result logs and
recording complete committed full-suite outcomes. Explain that selected-only
passes cannot supply the missing outcomes for a full-suite audit.

Language guides: Java/Maven, Gradle/multi-module/custom roots; Python/pytest/src
layout and project .venv; mixed-language limits. Add troubleshooting for missing
Git/JDK/build tool/Python/pytest, no discovered tests, stale history, failed audit,
unsupported files/builds, incomplete results and catalogue unavailable.

Agent guide documents plan/impact/check, server-side repository/build permission,
immutable snapshots, BASE policy pins, the default B10 versus opt-in CRC,
all verdicts and the meaning of audit denominator/sample size. Include real
examples with actual outputs, labelled synthetic when appropriate.

Every command must be checked against --help or a saved test. Keep examples
copyable on Windows and explain paths with spaces. Never put credentials or
private datasets in documentation snippets.

## 10. Research page and defensible novelty

Lead with the question and evaluated decision pipeline. Explain that a recent
failure ordering can be strong, and CodeDNA investigates when stopping on a risk
estimate is useful. Show the product's conservative refusal behavior.

Required evidence cards:

- Nine-project B10 confirmation: no meaningful matched-time safety advantage,
  with lower failing-test recall. Cite the saved study and uncertainty.
- B12f: target met on 8/9, with a time/safety tradeoff; Cloudify misses 95%.
- B13f: promising exploratory result, not independently confirmed superiority.
- PTS: attempted cost matching failed; no equal-cost winner established.
- Agent patch study: structural selection evaluated; no measured improvement to
  agents' code-writing quality. Keep primary and post-hoc results distinct.

Explain three losses: build escape (catch no failure), any omitted failure,
and missed-test fraction. Always display the denominator. A target over all
commits differs from one over failing commits. CRC's expected-risk correction
is not a 95%-confidence guarantee on every future commit.

Link protocols, findings, code/input hashes, reproducibility instructions and
limitations. Do not publish private data. Cite related work, including PTS,
DANTE, Westermo CRC, FaithfulCut, TDAD/TestPrune and conformal-risk methods.
The new partial-feedback research direction remains proposed until built and
independently evaluated. Keep its future-work status separate from shipped UI.

## 11. Visual design and accessibility

Use the IDE's visual identity: dark near-black background, restrained green
accent, warm amber for caution, red for actual failures. Suggested existing
values: background #07090d, panels #0f131a, text #e6e8eb, muted #9aa3ad,
accent #86b38a, warning #d8a657. Support a readable light theme.

Use a modern readable system/locally hosted sans-serif; monospaced code and
hashes. Respect font licences. Use generous spacing, short paragraphs and clear
visual hierarchy. Animate graph relationships sparingly; honor reduced-motion.
Avoid decorative animations that obscure evidence or slow student laptops.

Use semantic headings/navigation, keyboard-operable controls, visible focus,
labelled forms, text status as well as color, sufficient contrast, responsive
320px-to-desktop layouts, meaningful screenshot alt text and non-clipped long
hashes/paths. Test dropdowns, copy buttons, offline notices and narrow screens.

## 12. Assets and data contracts

Use current screenshots of Changes, Impact, Tests, History and Extensions.
Never show a made-up safety percentage in an unlabelled product screenshot.
Use a small sanitized example graph JSON for the interactive demonstration.
Keep catalogues/release metadata as validated JSON and separate marketing copy.

Catalogue version fields: exact version, plugin API version, bundled flag; for
optional downloads, official wheel URL and full SHA-256. Release fields: platform,
architecture, exact asset URL, SHA-256, bytes, signing status and release notes.
Unknown values remain unavailable; no placeholder URL should be clickable.

Website/backend responsibilities: static site renders public metadata; core does
analysis and installation checks; IDE displays core JSON and requests consent.
No accounts, cloud code upload, analytics or arbitrary plugin registry are needed.

## 13. Acceptance criteria and build sequence

First deliver responsive Home/Docs/Plugins/Downloads with correct links and
current capabilities. Then add current screenshots and Research evidence.
Publish real release assets only after the release gates in section 8 pass.

Acceptance checklist:

- A visitor can tell what CodeDNA does within the first screen.
- Java and Python appear as bundled; future languages are clearly planned.
- The app exposes Extensions → Language plugins after restart, including old layouts.
- Optional download metadata is official, pinned, checksummed and compatible.
- Browser downloads never silently install or talk to the local analysis API.
- Offline/invalid metadata gives a useful state; installed languages still work.
- All links, copy commands, keyboard navigation and mobile layouts are checked.
- No fabricated guarantee, speedup, public release, human label or approval appears.
- The published catalogue and app refer to one verified release source.

The current repository implements the plugin acquisition display and persistent
Extensions entry. Public hosting, optional frozen-desktop installation validation,
clean-PC acceptance and the independent research/human sign-offs remain release
gates. This blueprint is ready for the website builder; it does not conceal them.
