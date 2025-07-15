<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import loader from '@monaco-editor/loader';
  import type * as Monaco from 'monaco-editor/esm/vs/editor/editor.api';

  export let value: string = '';
  export let language: string = 'javascript';
  export let theme: string = 'vs-dark';
  export let readOnly: boolean = false;
  export let minimap: boolean = true;
  export let height: string = '400px';
  export let width: string = '100%';

  let container: HTMLDivElement;
  let editor: Monaco.editor.IStandaloneCodeEditor | null = null;
  let monaco: typeof Monaco | null = null;

  onMount(async () => {
    try {
      monaco = await loader.init();

      if (container && monaco) {
        editor = monaco.editor.create(container, {
          value,
          language,
          theme,
          readOnly,
          minimap: { enabled: minimap },
          fontSize: 14,
          lineNumbers: 'on',
          renderLineHighlight: 'all',
          automaticLayout: true,
          scrollBeyondLastLine: false,
          wordWrap: 'on',
          contextmenu: true,
          selectOnLineNumbers: true,
          roundedSelection: false,
          renderIndentGuides: true,
          cursorStyle: 'line',
          formatOnPaste: true,
          formatOnType: true,
          tabSize: 2,
          insertSpaces: true,
        });

        // Update value when editor content changes
        editor.onDidChangeModelContent(() => {
          if (editor && !readOnly) {
            value = editor.getValue();
          }
        });

        // Handle resize
        const resizeObserver = new ResizeObserver(() => {
          editor?.layout();
        });
        resizeObserver.observe(container);
      }
    } catch (error) {
      console.error('Failed to initialize Monaco Editor:', error);
    }
  });

  onDestroy(() => {
    editor?.dispose();
  });

  // Reactive updates
  $: if (editor && editor.getValue() !== value) {
    editor.setValue(value);
  }

  $: if (editor && monaco) {
    const model = editor.getModel();
    if (model && model.getLanguageId() !== language) {
      monaco.editor.setModelLanguage(model, language);
    }
  }

  $: if (editor) {
    editor.updateOptions({ readOnly });
  }

  // Public methods
  export function getValue(): string {
    return editor?.getValue() || '';
  }

  export function setValue(newValue: string): void {
    if (editor) {
      editor.setValue(newValue);
    }
  }

  export function focus(): void {
    editor?.focus();
  }

  export function getSelectedText(): string {
    if (editor) {
      const selection = editor.getSelection();
      if (selection) {
        return editor.getModel()?.getValueInRange(selection) || '';
      }
    }
    return '';
  }

  export function insertText(text: string): void {
    if (editor) {
      const selection = editor.getSelection();
      if (selection) {
        const operation = {
          range: selection,
          text,
          forceMoveMarkers: true,
        };
        editor.executeEdits('insert-text', [operation]);
      }
    }
  }

  // Language detection helper
  export function detectLanguage(filename: string): string {
    const ext = filename.split('.').pop()?.toLowerCase() || '';
    const languageMap: Record<string, string> = {
      js: 'javascript',
      ts: 'typescript',
      jsx: 'javascript',
      tsx: 'typescript',
      py: 'python',
      rb: 'ruby',
      php: 'php',
      java: 'java',
      cs: 'csharp',
      cpp: 'cpp',
      c: 'c',
      h: 'c',
      hpp: 'cpp',
      go: 'go',
      rs: 'rust',
      swift: 'swift',
      kt: 'kotlin',
      scala: 'scala',
      sh: 'shell',
      bash: 'shell',
      zsh: 'shell',
      ps1: 'powershell',
      html: 'html',
      htm: 'html',
      css: 'css',
      scss: 'scss',
      sass: 'sass',
      less: 'less',
      json: 'json',
      xml: 'xml',
      yaml: 'yaml',
      yml: 'yaml',
      toml: 'toml',
      ini: 'ini',
      cfg: 'ini',
      conf: 'ini',
      md: 'markdown',
      markdown: 'markdown',
      sql: 'sql',
      dockerfile: 'dockerfile',
      makefile: 'makefile',
      r: 'r',
      m: 'objective-c',
      mm: 'objective-c',
      pl: 'perl',
      lua: 'lua',
      dart: 'dart',
      clj: 'clojure',
      cljs: 'clojure',
      elm: 'elm',
      ex: 'elixir',
      exs: 'elixir',
      erl: 'erlang',
      hrl: 'erlang',
      fs: 'fsharp',
      fsx: 'fsharp',
      fsi: 'fsharp',
      ml: 'ocaml',
      mli: 'ocaml',
      hs: 'haskell',
      lhs: 'haskell',
      pas: 'pascal',
      pp: 'pascal',
      tex: 'latex',
      bib: 'bibtex',
    };
    return languageMap[ext] || 'plaintext';
  }
</script>

<div
  bind:this={container}
  class="monaco-editor-container"
  style="height: {height}; width: {width};"
/>

<style>
  .monaco-editor-container {
    border: 1px solid var(--color-border);
    border-radius: 8px;
    overflow: hidden;
    background: var(--color-surface);
  }

  :global(.monaco-editor) {
    font-family:
      'Monaco', 'Menlo', 'Ubuntu Mono', 'DejaVu Sans Mono', 'Courier New', monospace !important;
  }

  :global(.monaco-editor .margin) {
    background: var(--color-surface-variant) !important;
  }

  :global(.monaco-editor .current-line) {
    background: var(--color-primary-container) !important;
  }

  :global(.monaco-editor .selected-text) {
    background: var(--color-secondary-container) !important;
  }

  /* Dark theme adjustments */
  :global([data-theme='dark'] .monaco-editor) {
    --color-border: #3a3a3a;
    --color-surface: #1e1e1e;
    --color-surface-variant: #252526;
    --color-primary-container: #264f78;
    --color-secondary-container: #3a3d41;
  }

  /* Light theme adjustments */
  :global([data-theme='light'] .monaco-editor) {
    --color-border: #e1e4e8;
    --color-surface: #ffffff;
    --color-surface-variant: #f6f8fa;
    --color-primary-container: #e8f4ff;
    --color-secondary-container: #f0f3f6;
  }
</style>
