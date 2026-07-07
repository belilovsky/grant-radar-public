"""Local AV Design System token adapter for the server-rendered dashboard."""

from __future__ import annotations

AVDS_FONT_HEAD = ""

AVDS_CSS = """
    :root {
      --button-outline: rgb(15 23 42 / 0.10);
      --badge-outline: rgb(15 23 42 / 0.08);
      --radius: 8px;
      --av-color-blue-50: #eff6ff;
      --av-color-blue-100: #dbeafe;
      --av-color-blue-600: #2563eb;
      --av-color-blue-700: #1d4ed8;
      --av-color-blue-800: #1e40af;
      --av-color-slate-25: #fafbfc;
      --av-color-slate-50: #f8fafc;
      --av-color-slate-75: #eef1f4;
      --av-color-slate-100: #f1f5f9;
      --av-color-slate-200: #e2e8f0;
      --av-color-slate-300: #cbd5e1;
      --av-color-slate-400: #94a3b8;
      --av-color-slate-500: #64748b;
      --av-color-slate-700: #334155;
      --av-color-slate-900: #0f172a;
      --av-color-emerald-50: #ecfdf5;
      --av-color-emerald-100: #d1fae5;
      --av-color-emerald-700: #047857;
      --av-color-amber-50: #fffbeb;
      --av-color-amber-100: #fef3c7;
      --av-color-amber-700: #b45309;
      --av-color-red-50: #fef2f2;
      --av-color-red-100: #fee2e2;
      --av-color-red-600: #dc2626;
      --av-color-white: #ffffff;
      --av-spacing-0: 0;
      --av-spacing-1: 4px;
      --av-spacing-2: 8px;
      --av-spacing-3: 12px;
      --av-spacing-4: 16px;
      --av-spacing-5: 20px;
      --av-spacing-6: 24px;
      --av-spacing-8: 32px;
      --av-spacing-10: 40px;
      --av-spacing-12: 48px;
      --av-radius-sm: 4px;
      --av-radius-md: 8px;
      --av-radius-lg: 12px;
      --av-radius-full: 999px;
      --av-shadow-2xs: 0 1px 1px rgb(15 23 42 / 0.03);
      --av-shadow-xs: 0 1px 2px rgb(15 23 42 / 0.04);
      --av-shadow-sm: 0 1px 2px rgb(15 23 42 / 0.08);
      --av-shadow-md: 0 4px 8px rgb(15 23 42 / 0.06), 0 2px 4px rgb(15 23 42 / 0.04);
      --av-shadow-lg: 0 8px 16px rgb(15 23 42 / 0.08), 0 4px 8px rgb(15 23 42 / 0.04);
      --av-duration-base: 180ms;
      --av-easing-emphasized: cubic-bezier(0.2, 0, 0.1, 1);
      --motion-duration-base: var(--av-duration-base);
      --motion-easing-standard: var(--av-easing-emphasized);
      --av-container-dashboard: 1120px;
      --av-control-height-sm: 32px;
      --av-control-height-md: 36px;
      --av-card-padding-sm: 10px;
      --av-card-padding-md: 12px;
      --av-section-gap: 24px;
      --av-font-sans: Arial, "Helvetica Neue", Helvetica, system-ui, sans-serif;
      --av-font-serif: Georgia, ui-serif, serif;
      --av-font-mono: "Arial", ui-monospace, SFMono-Regular, Menlo, monospace;
      --font-sans: var(--av-font-sans);
      --font-serif: var(--av-font-serif);
      --font-mono: var(--av-font-mono);
      --av-text-xs: 12px;
      --av-text-sm: 13px;
      --av-text-md: 14px;
      --av-text-base: 15px;
      --av-text-lg: 17px;
      --av-text-xl: 20px;
      --av-text-2xl: 24px;
      --av-text-3xl: 30px;
      --av-text-4xl: 42px;
      --av-leading-tight: 1.2;
      --av-leading-snug: 1.35;
      --av-leading-normal: 1.5;
    }

    [data-av-theme="light"] {
      --av-color-background: var(--av-color-slate-25);
      --av-color-foreground: var(--av-color-slate-900);
      --av-color-surface: var(--av-color-white);
      --av-color-surface-subtle: var(--av-color-slate-50);
      --av-color-muted: var(--av-color-slate-100);
      --av-color-muted-foreground: var(--av-color-slate-500);
      --av-color-border: var(--av-color-slate-200);
      --av-color-border-strong: var(--av-color-slate-300);
      --av-color-border-subtle: rgb(226 232 240 / 0.72);
      --av-color-primary: var(--av-color-blue-700);
      --av-color-primary-hover: var(--av-color-blue-800);
      --av-color-primary-muted: var(--av-color-blue-100);
      --av-color-primary-subtle: var(--av-color-blue-50);
      --av-color-primary-foreground: var(--av-color-white);
      --av-color-surface-raised: color-mix(
        in oklab,
        var(--av-color-surface),
        var(--av-color-slate-50) 28%
      );
      --av-focus-ring: 0 0 0 3px color-mix(
        in oklab,
        var(--av-color-primary),
        transparent 72%
      );
      --shadow-focus: var(--av-focus-ring);
      --av-color-success: var(--av-color-emerald-700);
      --av-color-success-subtle: var(--av-color-emerald-50);
      --av-color-warning: var(--av-color-amber-700);
      --av-color-warning-subtle: var(--av-color-amber-50);
      --av-color-danger: var(--av-color-red-600);
      --av-color-danger-subtle: var(--av-color-red-50);
    }

    [data-theme="light"] {
      --color-bg: var(--av-color-background);
      --color-bg-subtle: var(--av-color-surface-subtle);
      --color-surface: var(--av-color-surface);
      --color-surface-raised: var(--av-color-surface-raised);
      --color-text: var(--av-color-foreground);
      --color-text-muted: var(--av-color-muted-foreground);
      --color-border: var(--av-color-border);
      --color-border-strong: var(--av-color-border-strong);
      --color-border-subtle: var(--av-color-border-subtle);
      --color-accent: var(--av-color-primary);
      --color-accent-hover: var(--av-color-primary-hover);
      --color-accent-subtle: var(--av-color-primary-subtle);
      --color-accent-muted: var(--av-color-primary-muted);
      --color-accent-contrast: var(--av-color-primary-foreground);
      --color-success: var(--av-color-success);
      --color-success-subtle: var(--av-color-success-subtle);
      --color-warning: var(--av-color-warning);
      --color-warning-subtle: var(--av-color-warning-subtle);
      --color-danger: var(--av-color-danger);
      --color-danger-subtle: var(--av-color-danger-subtle);
      --color-focus-ring: var(--av-focus-ring);
      --shadow-2xs: var(--av-shadow-2xs);
      --shadow-xs: var(--av-shadow-xs);
      --shadow-sm: var(--av-shadow-sm);
      --shadow-md: var(--av-shadow-md);
      --shadow-lg: var(--av-shadow-lg);
    }
"""
