/**
 * Generated by orval v7.10.0 🍺
 * Do not edit manually.
 * PRSNL
 * OpenAPI spec version: 6.0.0-beta.2
 */
import type { DevelopmentCategoryDescription } from './developmentCategoryDescription';
import type { DevelopmentCategoryItemCount } from './developmentCategoryItemCount';

export interface DevelopmentCategory {
  id: string;
  name: string;
  description?: DevelopmentCategoryDescription;
  icon?: string;
  color?: string;
  created_at: string;
  item_count?: DevelopmentCategoryItemCount;
}
