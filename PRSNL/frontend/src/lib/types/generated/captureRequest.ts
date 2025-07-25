/**
 * Generated by orval v7.10.0 🍺
 * Do not edit manually.
 * PRSNL
 * OpenAPI spec version: 6.0.0-beta.2
 */
import type { CaptureRequestUrl } from './captureRequestUrl';
import type { CaptureRequestContent } from './captureRequestContent';
import type { CaptureRequestTitle } from './captureRequestTitle';
import type { CaptureRequestHighlight } from './captureRequestHighlight';
import type { CaptureRequestTags } from './captureRequestTags';
import type { CaptureRequestUploadedFiles } from './captureRequestUploadedFiles';
import type { CaptureRequestProgrammingLanguage } from './captureRequestProgrammingLanguage';
import type { CaptureRequestProjectCategory } from './captureRequestProjectCategory';
import type { CaptureRequestDifficultyLevel } from './captureRequestDifficultyLevel';
import type { CaptureRequestIsCareerRelated } from './captureRequestIsCareerRelated';

export interface CaptureRequest {
  /** URL to capture */
  url?: CaptureRequestUrl;
  /** Direct content to save */
  content?: CaptureRequestContent;
  /** Title of the item */
  title?: CaptureRequestTitle;
  /** Highlighted text */
  highlight?: CaptureRequestHighlight;
  /** Tags for categorization */
  tags?: CaptureRequestTags;
  /** Enable AI summarization for this item */
  enable_summarization?: boolean;
  /** Content type: auto, document, video, article, tutorial, image, note, link, development */
  content_type?: string;
  /** Uploaded files for processing */
  uploaded_files?: CaptureRequestUploadedFiles;
  /** Programming language for development content */
  programming_language?: CaptureRequestProgrammingLanguage;
  /** Project category for development content */
  project_category?: CaptureRequestProjectCategory;
  /** Difficulty level (1-5) for development content */
  difficulty_level?: CaptureRequestDifficultyLevel;
  /** Whether this content is career/job related */
  is_career_related?: CaptureRequestIsCareerRelated;
}
