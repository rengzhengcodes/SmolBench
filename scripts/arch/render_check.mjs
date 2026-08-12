/**
 * Headless render check for the atlas page.
 *
 * The page builds its whole DOM at runtime from one JSON blob, so a mistake in
 * the renderer produces a blank section rather than a build error -- nothing
 * upstream would catch it. This runs the page's own script against a minimal
 * `document` stub and asserts on the HTML it produces.
 *
 * It deliberately re-reads the script out of the built page on every run. An
 * earlier version of this harness inlined a copy of the script when it was
 * written, and then silently kept reporting faults from a stale copy after the
 * template had been fixed.
 *
 * Usage: `node scripts/arch/render_check.mjs`
 * Exits non-zero on any empty region, leaked placeholder, or SVG label that
 * would overrun its box.
 */

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const PAGE = path.join(HERE, "model_architectures.html");

const html = fs.readFileSync(PAGE, "utf8");
const raw = html.match(/id="page-data">([\s\S]*?)<\/script>/)[1];
const script = html.match(/<script>\n(\(function \(\) \{[\s\S]*?)\n<\/script>/)[1];

const els = {};
globalThis.document = {
  getElementById(id) {
    if (!els[id]) els[id] = { id, innerHTML: "", textContent: id === "page-data" ? raw : "" };
    return els[id];
  }
};

const problems = [];
try {
  (0, eval)(script);
} catch (err) {
  console.error("renderer threw:", err && err.stack || err);
  process.exit(1);
}

const REGIONS = ["standfirst", "masthead-stats", "read-body", "read-notes", "legend",
                 "roster-list", "position-body", "position-chart", "position-notes",
                 "families", "matrix-table", "method-body", "footer-body"];
for (const id of REGIONS) {
  if (!els[id] || !els[id].innerHTML.length) problems.push(`empty region: #${id}`);
}

const data = JSON.parse(raw);
const nModels = Object.keys(data.models).length;
const fam = els["families"].innerHTML;
const cards = (fam.match(/class="model"/g) || []).length;
const strips = (els["roster-list"].innerHTML.match(/<svg/g) || []).length;
const figs = (fam.match(/<svg/g) || []).length;
if (cards !== nModels) problems.push(`${cards} model cards for ${nModels} models`);
if (strips !== nModels) problems.push(`${strips} roster strips for ${nModels} models`);
if (figs !== nModels * 2) problems.push(`${figs} diagrams, expected ${nModels * 2}`);

// Leaked JS values. Scoped to attribute values and bare text nodes, because
// the words themselves legitimately appear in the prose -- one model's flag
// says its chat template leaves `enable_thinking` undefined, and a naive
// substring search reports that as a rendering fault.
const all = Object.values(els).map((e) => e.innerHTML).join("");
const proseStripped = all.replace(/<code>[\s\S]*?<\/code>/g, "");
for (const token of ["undefined", "NaN", "[object Object]", "__PAGE_DATA__"]) {
  const patterns = [
    new RegExp(`=["'][^"']*${token.replace(/[[\]]/g, "\\$&")}`, "g"),
    new RegExp(`>\\s*${token.replace(/[[\]]/g, "\\$&")}\\s*<`, "g")
  ];
  for (const re of patterns) {
    const hit = re.exec(proseStripped);
    if (hit) {
      problems.push(`leaked ${token} — context: ` +
        JSON.stringify(proseStripped.slice(Math.max(0, hit.index - 120), hit.index + 40)));
      break;
    }
  }
}

// Unconverted markdown. The annotations are written with `**bold**` and
// `*italic*`; a formatter that misses them prints the asterisks verbatim, which
// is invisible to every other check here. Code spans are excluded -- `**kwargs`
// and `head_dim**-0.5` are legitimately literal.
const outsideCode = all.replace(/<code>[\s\S]*?<\/code>/g, "");
const unconvertedBold = (outsideCode.match(/\*\*/g) || []).length;
if (unconvertedBold) {
  const i = outsideCode.indexOf("**");
  problems.push(`${unconvertedBold} unconverted **bold** run(s) — context: ` +
    JSON.stringify(outsideCode.slice(Math.max(0, i - 100), i + 40)));
}

// Every schematic label is left-anchored monospace inside a 452-unit box.
// 0.6 em advance is the common width for every ui-monospace face.
const overflow = [];
const TEXT = /<text x="([\d.]+)" y="[\d.]+" font-size="([\d.]+)"([^>]*)>([^<]*)<\/text>/g;
let m;
while ((m = TEXT.exec(fam))) {
  if (/text-anchor/.test(m[3])) continue;
  const right = parseFloat(m[1]) + m[4].length * parseFloat(m[2]) * 0.6;
  if (right > 466) overflow.push(`${right.toFixed(0)}u  ${JSON.stringify(m[4])}`);
}
if (overflow.length) {
  problems.push(`${overflow.length} schematic label(s) overrun the 466u box:`);
  overflow.sort().slice(0, 8).forEach((line) => problems.push("    " + line));
}

// Strips must share one aspect ratio per context, or the roster stops being
// comparable: a 26-layer stack would render three times taller than a 92-layer one.
for (const [label, id] of [["roster", "roster-list"], ["model", "families"]]) {
  const ratios = new Set([...els[id].innerHTML.matchAll(/class="strip" viewBox="0 0 ([\d.]+) ([\d.]+)"/g)]
    .map((r) => (parseFloat(r[1]) / parseFloat(r[2])).toFixed(2)));
  if (ratios.size !== 1) problems.push(`${label} strips have ${ratios.size} aspect ratios: ${[...ratios]}`);
}

const annotated = Object.values(data.models).filter((mm) => mm.note && Object.keys(mm.note).length).length;
console.log(`regions ${REGIONS.length} · models ${nModels} · cards ${cards} · diagrams ${figs} · annotated ${annotated}/${nModels}`);
if (problems.length) {
  console.log("\nPROBLEMS:");
  problems.forEach((p) => console.log("  " + p));
  process.exit(1);
}
console.log("render check OK");
