export interface Conversation {
  id: string;
  title: string;
  model_provider: string;
  model_name: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  messages?: Message[];
}

export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system' | 'tool';
  content: string;
  components?: UIComponent[] | null;
  tool_calls?: ToolCallLog[] | null;
  created_at: string;
}

export interface ToolCallLog {
  tool: string;
  args: Record<string, unknown>;
  result: unknown;
}

// UI Components returned by the AI
export type UIComponent =
  | StatCardComponent
  | TableComponent
  | BarChartComponent
  | PieChartComponent
  | LineChartComponent
  | DetailCardComponent
  | ConfirmationDialogComponent
  | FormComponent;

export interface StatCardComponent {
  type: 'stat_card';
  label: string;
  value: string | number;
  description?: string;
  trend?: string;
}

export interface TableComponent {
  type: 'table';
  title?: string;
  columns: string[];
  rows: (string | number | null)[][];
}

export interface BarChartComponent {
  type: 'bar_chart';
  title?: string;
  data: Record<string, string | number>[];
  x_key: string;
  y_key: string;
}

export interface PieChartComponent {
  type: 'pie_chart';
  title?: string;
  data: { name: string; value: number }[];
}

export interface LineChartComponent {
  type: 'line_chart';
  title?: string;
  data: Record<string, string | number>[];
  x_key: string;
  y_key: string;
}

export interface DetailCardComponent {
  type: 'detail_card';
  title?: string;
  fields: { label: string; value: string }[];
}

export interface ConfirmationDialogComponent {
  type: 'confirmation_dialog';
  title: string;
  description: string;
  action: string;
  parameters: Record<string, unknown>;
  requires_confirmation: boolean;
}

export interface FormComponent {
  type: 'form';
  title: string;
  fields: FormField[];
  action: string;
}

export interface FormField {
  name: string;
  label: string;
  type: 'text' | 'number' | 'select';
  required?: boolean;
  options?: { label: string; value: string }[];
  default_value?: string;
}

// SSE events
export interface SSEEvent {
  event: string;
  data: Record<string, unknown>;
}

export interface ModelInfo {
  provider: string;
  models: string[];
  is_available: boolean;
}
