import { readFileSync } from 'node:fs';
import { createHighlighterCore } from 'shiki/core';
import { createOnigurumaEngine } from 'shiki/engine/oniguruma';
import { bundledLanguages } from 'shiki/langs';

const theme = {
  name: 'html-theme',
  colors: {
    'editor.foreground': 'var(--text)',
    'editor.background': 'var(--sunken)',
  },
  tokenColors: [
    { scope: ['comment'], settings: { foreground: 'var(--text-muted)', fontStyle: 'italic' } },
    { scope: ['keyword', 'storage'], settings: { foreground: 'var(--text-strong)', fontStyle: 'bold' } },
    { scope: ['entity.name.function', 'support.function', 'entity.name.type', 'support.type'], settings: { foreground: 'var(--text-strong)' } },
  ],
};
const plainLanguages = new Set(['text', 'txt', 'plain', 'plaintext']);

function escapeHtml(source) {
  return source.replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;');
}

function renderToken(token) {
  const classes = [];
  if (token.color === 'var(--text-strong)') classes.push('syntax-strong');
  if (token.color === 'var(--text-muted)') classes.push('syntax-muted');
  if (token.fontStyle > 0) {
    if (token.fontStyle & 1) classes.push('syntax-italic');
    if (token.fontStyle & 2) classes.push('syntax-bold');
  }
  const text = escapeHtml(token.content);
  if (classes.length === 0) return text;
  return `<span class="${classes.join(' ')}">${text}</span>`;
}

async function highlight(snippets) {
  const languages = [...new Set(snippets.map(snippet => snippet.language))]
    .filter(language => Object.hasOwn(bundledLanguages, language));
  const warnings = new Set();
  let highlighter;
  if (languages.length > 0) {
    highlighter = await createHighlighterCore({
      themes: [theme],
      langs: await Promise.all(languages.map(language => bundledLanguages[language]())),
      engine: createOnigurumaEngine(import('shiki/wasm')),
    });
  }
  try {
    const output = snippets.map(snippet => {
      if (plainLanguages.has(snippet.language)) {
        return { html: escapeHtml(snippet.source), highlighted: false };
      }
      if (!Object.hasOwn(bundledLanguages, snippet.language)) {
        warnings.add(`Unknown code language '${snippet.language}'; kept its source as plain text.`);
        return { html: escapeHtml(snippet.source), highlighted: false };
      }
      const lines = highlighter.codeToTokensBase(snippet.source, { lang: snippet.language, theme: theme.name });
      const endings = snippet.source.match(/\r?\n/g) || [];
      const source = lines.map((line, index) => line.map(token => token.content).join('') + (endings[index] || '')).join('');
      if (source !== snippet.source) {
        throw new Error(`Highlighting changed the source text for '${snippet.language}'.`);
      }
      const html = lines.map((line, index) => line.map(renderToken).join('') + (endings[index] || '')).join('');
      return { html, highlighted: true };
    });
    return { snippets: output, warnings: [...warnings] };
  } finally {
    highlighter?.dispose();
  }
}

try {
  const snippets = JSON.parse(readFileSync(0, 'utf8'));
  process.stdout.write(JSON.stringify(await highlight(snippets)));
} catch (error) {
  console.error(error instanceof Error ? error.message : String(error));
  process.exitCode = 1;
}
