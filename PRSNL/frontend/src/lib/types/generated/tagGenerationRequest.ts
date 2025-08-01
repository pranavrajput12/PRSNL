/**
 * Generated by orval v7.10.0 🍺
 * Do not edit manually.
 * PRSNL
 * OpenAPI spec version: 6.0.0-beta.2
 */

/**
 * Request model for tag generation.
 */
export interface TagGenerationRequest {
  /**
   * @minLength 1
   * @maxLength 50000
   */
  content: string;
  /**
   * @minimum 1
   * @maximum 20
   */
  limit?: number;
  language?: string;
}
