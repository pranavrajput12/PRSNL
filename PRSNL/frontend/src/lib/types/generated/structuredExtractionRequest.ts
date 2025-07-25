/**
 * Generated by orval v7.10.0 🍺
 * Do not edit manually.
 * PRSNL
 * OpenAPI spec version: 6.0.0-beta.2
 */
import type { StructuredExtractionRequestSchema } from './structuredExtractionRequestSchema';
import type { StructuredExtractionRequestExtractionPrompt } from './structuredExtractionRequestExtractionPrompt';

/**
 * Request model for structured data extraction
 */
export interface StructuredExtractionRequest {
  /**
   * URL to extract from
   * @minLength 1
   * @maxLength 2083
   */
  url: string;
  /** JSON schema for extraction */
  schema: StructuredExtractionRequestSchema;
  /** Custom extraction prompt */
  extraction_prompt?: StructuredExtractionRequestExtractionPrompt;
}
