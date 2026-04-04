import type { UIComponent } from '../types/chat';

interface ParsedAssistantContent {
  text: string;
  components: UIComponent[];
}

export interface AssistantRenderState {
  text: string;
  components: UIComponent[];
  hideRawContent: boolean;
}

const COMPONENT_TYPES = new Set([
  'stat_card',
  'table',
  'bar_chart',
  'pie_chart',
  'line_chart',
  'detail_card',
  'confirmation_dialog',
  'form',
]);

function stripCodeFence(content: string): string {
  const trimmed = content.trim();
  if (trimmed.startsWith('```json')) {
    const inner = trimmed.slice(7).trim();
    return inner.endsWith('```') ? inner.slice(0, -3).trim() : inner;
  }
  if (trimmed.startsWith('```')) {
    const inner = trimmed.slice(3).trim();
    return inner.endsWith('```') ? inner.slice(0, -3).trim() : inner;
  }
  return trimmed;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function isUIComponent(value: unknown): value is UIComponent {
  return isRecord(value) && typeof value.type === 'string' && COMPONENT_TYPES.has(value.type);
}

function parseAssistantContent(content: string): ParsedAssistantContent | null {
  const trimmed = stripCodeFence(content);
  if (!trimmed) {
    return null;
  }

  try {
    const parsed: unknown = JSON.parse(trimmed);

    if (isRecord(parsed) && ('text' in parsed || 'components' in parsed)) {
      const text = typeof parsed.text === 'string' ? parsed.text : '';
      const components = Array.isArray(parsed.components)
        ? parsed.components.filter(isUIComponent)
        : [];
      return { text, components };
    }

    if (isUIComponent(parsed)) {
      return { text: '', components: [parsed] };
    }

    if (Array.isArray(parsed) && parsed.every(isUIComponent)) {
      return { text: '', components: parsed };
    }
  } catch {
    return null;
  }

  return null;
}

export function looksLikeStructuredAssistantContent(content: string): boolean {
  const trimmed = content.trim();
  if (!trimmed) {
    return false;
  }

  if (trimmed.startsWith('```json') || trimmed.startsWith('```')) {
    return true;
  }

  if (!(trimmed.startsWith('{') || trimmed.startsWith('['))) {
    return false;
  }

  return (
    trimmed.includes('"components"') ||
    trimmed.includes('"type"') ||
    trimmed.includes('"columns"') ||
    trimmed.includes('"rows"')
  );
}

export function resolveAssistantRenderState(
  content: string,
  fallbackComponents?: UIComponent[] | null
): AssistantRenderState {
  const parsed = parseAssistantContent(content);
  const components = fallbackComponents?.length ? fallbackComponents : parsed?.components ?? [];

  if (parsed) {
    return {
      text: parsed.text,
      components,
      hideRawContent: true,
    };
  }

  if (looksLikeStructuredAssistantContent(content)) {
    return {
      text: '',
      components,
      hideRawContent: true,
    };
  }

  return {
    text: content,
    components,
    hideRawContent: false,
  };
}
