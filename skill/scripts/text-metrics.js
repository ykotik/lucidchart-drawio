#!/usr/bin/env node
/**
 * text-metrics.js — label size measurement for drawio-architect plans
 *
 * Reads a plan JSON (shapes + containers with label/style/width/height),
 * measures each label using a char-width table derived from Arial metrics,
 * and annotates every element with a `text_safe` block:
 *
 *   {
 *     min_width:    number,   // narrowest box that prevents wrapping
 *     min_height:   number,   // height for all lines at declared width
 *     line_count:   number,
 *     overflow:     boolean,  // true if declared dims are smaller than min
 *     method:       "char-table" | "canvas",
 *     wrapped_lines: string[]
 *   }
 *
 * For swimlane containers, also adds:
 *   text_safe.min_startSize  — min header height to fit the label
 *
 * Usage:
 *   node text-metrics.js plan.json                     # stdout
 *   node text-metrics.js plan.json --out out.json      # file
 *   node text-metrics.js plan.json --canvas            # try canvas first
 *   node text-metrics.js plan.json --strict            # exit 1 if any overflow
 *   echo '{"shapes":[...]}' | node text-metrics.js     # stdin
 *
 * Zero native dependencies by default.
 * With --canvas: tries require('canvas'); falls back silently if unavailable.
 */

'use strict';

// ─── constants ──────────────────────────────────────────────────────────────

const PADDING_H = 8;   // draw.io default horizontal label inset (each side)
const PADDING_V = 4;   // vertical inset (each side)
const LINE_HEIGHT_FACTOR = 1.4;   // line height = fontSize * factor

// Arial character widths at 11px (measured from browser canvas, normal weight).
// Keys: individual characters. 'default' = average fallback for unmeasured chars.
// Scale by (fontSize / 11) for other sizes, multiply by 1.08 for bold.
const ARIAL_11_WIDTHS = {
  ' ': 3.1,
  '!': 3.6, '"': 4.4, '#': 7.7, '$': 6.2, '%': 9.2, '&': 7.7, "'": 2.4,
  '(': 3.7, ')': 3.7, '*': 5.4, '+': 8.2, ',': 3.1, '-': 3.7, '.': 3.1, '/': 3.5,
  '0': 6.2, '1': 6.2, '2': 6.2, '3': 6.2, '4': 6.2, '5': 6.2, '6': 6.2,
  '7': 6.2, '8': 6.2, '9': 6.2,
  ':': 3.1, ';': 3.1, '<': 8.2, '=': 8.2, '>': 8.2, '?': 5.5, '@': 11.3,
  'A': 7.4, 'B': 7.0, 'C': 7.2, 'D': 7.8, 'E': 6.5, 'F': 6.0, 'G': 7.7,
  'H': 7.8, 'I': 2.9, 'J': 4.4, 'K': 7.2, 'L': 6.0, 'M': 9.0, 'N': 7.8,
  'O': 8.2, 'P': 6.6, 'Q': 8.2, 'R': 7.2, 'S': 6.4, 'T': 6.6, 'U': 7.8,
  'V': 7.4, 'W': 9.8, 'X': 6.9, 'Y': 6.6, 'Z': 6.9,
  '[': 3.7, '\\': 3.5, ']': 3.7, '^': 8.2, '_': 6.2, '`': 3.7,
  'a': 6.0, 'b': 6.4, 'c': 5.5, 'd': 6.4, 'e': 6.0, 'f': 3.4, 'g': 6.4,
  'h': 6.4, 'i': 2.7, 'j': 2.7, 'k': 6.0, 'l': 2.7, 'm': 9.6, 'n': 6.4,
  'o': 6.4, 'p': 6.4, 'q': 6.4, 'r': 3.8, 's': 5.2, 't': 4.0, 'u': 6.4,
  'v': 5.8, 'w': 7.8, 'x': 5.8, 'y': 5.8, 'z': 5.5,
  '{': 3.7, '|': 2.9, '}': 3.7, '~': 8.2,
  default: 6.2,
};

// ─── style parsing ───────────────────────────────────────────────────────────

function parseStyle(styleStr) {
  const kv = {};
  (styleStr || '').split(';').forEach(part => {
    const eq = part.indexOf('=');
    if (eq !== -1) {
      kv[part.slice(0, eq).trim()] = part.slice(eq + 1).trim();
    } else if (part.trim()) {
      kv[part.trim()] = '1';
    }
  });
  return {
    fontSize:   parseFloat(kv.fontSize  || '11'),
    fontStyle:  parseInt(kv.fontStyle   || '0', 10),
    isBold:     (parseInt(kv.fontStyle  || '0', 10) & 1) !== 0,
    isItalic:   (parseInt(kv.fontStyle  || '0', 10) & 2) !== 0,
    isSwimlane: (styleStr || '').includes('swimlane'),
    startSize:  parseFloat(kv.startSize || '26'),
    horizontal: (kv.horizontal || '1') !== '0',
    whiteSpace: kv.whiteSpace || 'wrap',
  };
}

// ─── HTML label parsing ──────────────────────────────────────────────────────

/**
 * Parse an mxCell HTML-ish label into an array of styled segments per line.
 * Returns: Array<{ text: string, fontSize: number, bold: boolean }>[]
 * (outer array = lines, inner array = runs within a line)
 */
function parseLabel(raw, defaultFontSize, defaultBold) {
  if (!raw) return [[{ text: '', fontSize: defaultFontSize, bold: defaultBold }]];

  // Decode common entities
  let s = raw
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&#xa;/gi, '\n')
    .replace(/&nbsp;/g, ' ');

  // Normalize <br/> variants to \n
  s = s.replace(/<br\s*\/?>/gi, '\n');

  // Walk the string collecting text runs, tracking bold/fontSize state
  const lines = [];
  let currentLine = [];
  let bold = defaultBold;
  let fontSize = defaultFontSize;
  const boldStack = [defaultBold];
  const sizeStack = [defaultFontSize];

  let i = 0;
  let textBuf = '';

  const flushBuf = () => {
    if (textBuf) {
      currentLine.push({ text: textBuf, fontSize, bold });
      textBuf = '';
    }
  };

  while (i < s.length) {
    if (s[i] === '\n') {
      flushBuf();
      lines.push(currentLine);
      currentLine = [];
      i++;
      continue;
    }
    if (s[i] === '<') {
      const close = s.indexOf('>', i);
      if (close === -1) { textBuf += s[i++]; continue; }
      const tag = s.slice(i + 1, close).trim();
      i = close + 1;

      if (/^b$/i.test(tag)) {
        flushBuf(); boldStack.push(true); bold = true;
      } else if (/^\/b$/i.test(tag)) {
        flushBuf(); boldStack.pop(); bold = boldStack[boldStack.length - 1];
      } else if (/^strong$/i.test(tag)) {
        flushBuf(); boldStack.push(true); bold = true;
      } else if (/^\/strong$/i.test(tag)) {
        flushBuf(); boldStack.pop(); bold = boldStack[boldStack.length - 1];
      } else if (/^span/i.test(tag)) {
        flushBuf();
        const m = tag.match(/font-size\s*:\s*([\d.]+)px/i);
        if (m) { sizeStack.push(parseFloat(m[1])); fontSize = parseFloat(m[1]); }
        else sizeStack.push(fontSize);
      } else if (/^\/span$/i.test(tag)) {
        flushBuf(); sizeStack.pop(); fontSize = sizeStack[sizeStack.length - 1];
      }
      // ignore other tags (div, p, etc.)
      continue;
    }
    textBuf += s[i++];
  }
  flushBuf();
  lines.push(currentLine);

  // Drop trailing empty line if label ends with <br/>
  if (lines.length > 1 && lines[lines.length - 1].every(r => r.text === '')) {
    lines.pop();
  }
  return lines;
}

// ─── char-table measurement ──────────────────────────────────────────────────

// CJK / emoji codepoint ranges → width factor relative to fontSize.
// A factor of 1.0 means the glyph is ~1 em wide (square CJK cell).
// A factor of 1.2 means the emoji is slightly wider than 1 em.
// We store as (factor * 11) so the existing (fontSize/11) scale applies.
const CJK_RANGES = [
  // [lo, hi, factor * 11]
  [0x3040, 0x309F, 11.0],   // Hiragana
  [0x30A0, 0x30FF, 11.0],   // Katakana
  [0x3400, 0x4DBF, 11.0],   // CJK Extension A
  [0x4E00, 0x9FFF, 11.0],   // CJK Unified Ideographs
  [0xAC00, 0xD7AF, 11.0],   // Hangul Syllables
  [0xFF00, 0xFFEF, 11.0],   // Fullwidth Forms
  [0x2600, 0x27BF, 13.2],   // Misc symbols / Dingbats (emoji-like)
  [0x1F300, 0x1F9FF, 13.2], // Emoji (Misc Symbols and Pictographs, Transport, etc.)
];

function cjkBase(cp) {
  for (const [lo, hi, base] of CJK_RANGES) {
    if (cp >= lo && cp <= hi) return base;
  }
  return null;
}

function charWidth(ch, fontSize, bold) {
  const cp = ch.codePointAt(0);
  const cjk = cjkBase(cp);
  const base = cjk !== null ? cjk : (ARIAL_11_WIDTHS[ch] ?? ARIAL_11_WIDTHS.default);
  return base * (fontSize / 11) * (bold ? 1.08 : 1.0);
}

function measureText_charTable(text, fontSize, bold) {
  let w = 0;
  for (const ch of text) w += charWidth(ch, fontSize, bold);
  return w;
}

// ─── canvas measurement (opt-in) ─────────────────────────────────────────────

let _canvasCtx = null;
function getCanvasCtx() {
  if (_canvasCtx) return _canvasCtx;
  try {
    const { createCanvas } = require('canvas');
    _canvasCtx = createCanvas(1, 1).getContext('2d');
    return _canvasCtx;
  } catch (_) {
    return null;
  }
}

function measureText_canvas(text, fontSize, bold) {
  const ctx = getCanvasCtx();
  if (!ctx) return null;
  ctx.font = `${bold ? 'bold ' : ''}${fontSize}px Arial, Helvetica, sans-serif`;
  return ctx.measureText(text).width;
}

// ─── core wrapping algorithm ──────────────────────────────────────────────────

/**
 * Given parsed label lines and a target content width, compute wrapped layout.
 *
 * @param {Array} parsedLines  — output of parseLabel()
 * @param {number} targetWidth — content width = declared_width - 2*PADDING_H
 * @param {boolean} useCanvas
 * @returns {{ wrappedLines: string[], maxLineWidth: number, totalHeight: number, lineCount: number }}
 */
function wrapLines(parsedLines, targetWidth, useCanvas) {
  const measure = (text, fontSize, bold) => {
    if (useCanvas) {
      const w = measureText_canvas(text, fontSize, bold);
      if (w !== null) return w;
    }
    return measureText_charTable(text, fontSize, bold);
  };

  const wrappedLines = [];
  let maxLineWidth = 0;
  let totalHeight = 0;

  for (const runs of parsedLines) {
    // Flatten runs into words, keeping font metadata per word
    const words = [];
    for (const run of runs) {
      const toks = run.text.split(/(\s+)/);
      for (const tok of toks) {
        if (tok) words.push({ text: tok, fontSize: run.fontSize, bold: run.bold });
      }
    }

    if (words.length === 0) {
      // Blank line — still contributes height
      const fs = runs[0]?.fontSize ?? 11;
      totalHeight += fs * LINE_HEIGHT_FACTOR;
      wrappedLines.push('');
      continue;
    }

    // Greedy word-wrap
    let lineText = '';
    let lineW = 0;
    let lineMaxFontSize = 0;

    const flushLine = (text, w, fs) => {
      wrappedLines.push(text.trimEnd());
      if (w > maxLineWidth) maxLineWidth = w;
      totalHeight += fs * LINE_HEIGHT_FACTOR;
    };

    for (const word of words) {
      const ww = measure(word.text, word.fontSize, word.bold);
      lineMaxFontSize = Math.max(lineMaxFontSize, word.fontSize);

      if (lineW === 0) {
        // First word on line — always place even if it exceeds targetWidth
        lineText += word.text;
        lineW += ww;
      } else if (word.text.match(/^\s+$/)) {
        // Whitespace token — add to buffer only if we haven't exceeded width
        if (lineW + ww <= targetWidth) {
          lineText += word.text;
          lineW += ww;
        }
      } else if (lineW + ww > targetWidth) {
        // Would overflow — flush current line, start new
        flushLine(lineText, lineW, lineMaxFontSize);
        lineText = word.text;
        lineW = ww;
        lineMaxFontSize = word.fontSize;
      } else {
        lineText += word.text;
        lineW += ww;
      }
    }
    if (lineText) flushLine(lineText, lineW, lineMaxFontSize);
  }

  return {
    wrappedLines,
    maxLineWidth: Math.ceil(maxLineWidth),
    totalHeight:  Math.ceil(totalHeight),
    lineCount: wrappedLines.length,
  };
}

// ─── per-element analysis ────────────────────────────────────────────────────

function analyzeElement(el, useCanvas) {
  const style   = parseStyle(el.style || '');
  const label   = el.label || '';
  const declW   = el.width  || 160;
  const declH   = el.height || 64;

  const method = (useCanvas && getCanvasCtx()) ? 'canvas' : 'char-table';

  if (style.isSwimlane) {
    // Swimlane: label lives in the header band
    // For horizontal swimlane (horizontal=1, default): header is at top, height = startSize, width = full width
    // For vertical swimlane (horizontal=0): header is left strip, width = startSize, height = full height
    const headerW = style.horizontal ? declW : style.startSize;
    const headerH = style.horizontal ? style.startSize : declH;
    const contentW = headerW - 2 * PADDING_H;
    const parsed = parseLabel(label, style.fontSize, style.isBold);
    const layout = wrapLines(parsed, contentW, useCanvas);
    const minH = layout.totalHeight + 2 * PADDING_V;
    const minW = layout.maxLineWidth + 2 * PADDING_H;
    const minStartSize = style.horizontal
      ? Math.ceil(minH)
      : Math.ceil(minW);

    return {
      min_width:      Math.max(minW, 80),
      min_height:     declH,   // container height is content-driven, not label-driven
      min_startSize:  Math.max(minStartSize, style.startSize),
      line_count:     layout.lineCount,
      overflow:       minStartSize > style.startSize,
      method,
      wrapped_lines:  layout.wrappedLines,
    };
  }

  // Regular node
  const contentW = declW - 2 * PADDING_H;
  const parsed   = parseLabel(label, style.fontSize, style.isBold);
  const layout   = wrapLines(parsed, contentW, useCanvas);

  // min_width = width that fits the longest word on one line (no wrapping at all)
  const noWrapLayout = wrapLines(parsed, Infinity, useCanvas);
  const minWidth  = noWrapLayout.maxLineWidth + 2 * PADDING_H;
  const minHeight = layout.totalHeight + 2 * PADDING_V;

  return {
    min_width:    Math.max(Math.ceil(minWidth), 80),
    min_height:   Math.max(Math.ceil(minHeight), 32),
    line_count:   layout.lineCount,
    overflow:     declW < minWidth || declH < minHeight,
    method,
    wrapped_lines: layout.wrappedLines,
  };
}

// ─── annotate plan ───────────────────────────────────────────────────────────

function annotatePlan(plan, useCanvas) {
  const annotated = JSON.parse(JSON.stringify(plan)); // deep clone

  for (const kind of ['shapes', 'containers']) {
    for (const el of annotated[kind] || []) {
      el.text_safe = analyzeElement(el, useCanvas);
      // Convenience aliases for fit-fonts.py --metrics lookup (keyed by el.id)
      el.text_safe.min_w = el.text_safe.min_width;
      el.text_safe.min_h = el.text_safe.min_height;
    }
  }
  return annotated;
}

// ─── CLI ──────────────────────────────────────────────────────────────────────

function main() {
  const args = process.argv.slice(2);
  let inputFile = null;
  let outputFile = null;
  let useCanvas = false;
  let strict = false;

  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--out' && args[i + 1]) { outputFile = args[++i]; }
    else if (args[i] === '--canvas') { useCanvas = true; }
    else if (args[i] === '--strict') { strict = true; }
    else if (!args[i].startsWith('-')) { inputFile = args[i]; }
  }

  // Read input
  let raw;
  if (inputFile) {
    const fs = require('fs');
    raw = fs.readFileSync(inputFile, 'utf8');
  } else {
    // stdin
    const chunks = [];
    process.stdin.setEncoding('utf8');
    process.stdin.on('data', d => chunks.push(d));
    process.stdin.on('end', () => {
      run(chunks.join(''), outputFile, useCanvas, strict);
    });
    return;
  }
  run(raw, outputFile, useCanvas, strict);
}

function run(raw, outputFile, useCanvas, strict) {
  let plan;
  try {
    plan = JSON.parse(raw);
  } catch (e) {
    process.stderr.write(`text-metrics: invalid JSON: ${e.message}\n`);
    process.exit(2);
  }

  const annotated = annotatePlan(plan, useCanvas);

  // Collect overflows for summary + strict mode
  const overflows = [];
  for (const kind of ['shapes', 'containers']) {
    for (const el of annotated[kind] || []) {
      if (el.text_safe?.overflow) {
        overflows.push({
          id: el.id,
          kind: kind.slice(0, -1),
          label: (el.label || '').slice(0, 40),
          declW: el.width, declH: el.height,
          minW:  el.text_safe.min_width,
          minH:  el.text_safe.min_height,
          minSS: el.text_safe.min_startSize,
        });
      }
    }
  }

  const out = JSON.stringify(annotated, null, 2);

  if (outputFile) {
    require('fs').writeFileSync(outputFile, out, 'utf8');
    process.stderr.write(`text-metrics: wrote ${outputFile}\n`);
  } else {
    process.stdout.write(out + '\n');
  }

  // Summary to stderr (doesn't pollute JSON stdout)
  const total = (plan.shapes?.length || 0) + (plan.containers?.length || 0);
  const method = (useCanvas && getCanvasCtx()) ? 'canvas' : 'char-table';
  process.stderr.write(`text-metrics: ${total} elements measured (${method}), ${overflows.length} overflow(s)\n`);

  if (overflows.length > 0) {
    for (const o of overflows) {
      const detail = o.minSS != null
        ? `startSize ${o.minSS} recommended (declared startSize in style)`
        : `min ${o.minW}×${o.minH}px (declared ${o.declW}×${o.declH}px)`;
      process.stderr.write(`  OVERFLOW  ${o.kind} '${o.id}' — "${o.label}" — ${detail}\n`);
    }
    if (strict) process.exit(1);
  }
}

main();
