/* generated using openapi-typescript-codegen -- do no edit */

/* istanbul ignore file */

/* tslint:disable */

/* eslint-disable */
import type { Citation } from './Citation';
import type { Document } from './Document';
import type { File } from './File';
import type { MessageAgent } from './MessageAgent';
import type { ToolCall } from './ToolCall';

export type Message = {
  text: string;
  id: string;
  created_at: string;
  updated_at: string;
  generation_id: string | null;
  position: number;
  is_active: boolean;
  documents: Array<Document>;
  citations: Array<Citation>;
  files: Array<File>;
  tool_calls: Array<ToolCall>;
  tool_plan: string | null;
  agent: MessageAgent;
};
