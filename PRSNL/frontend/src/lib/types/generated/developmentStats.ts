/**
 * Generated by orval v7.10.0 🍺
 * Do not edit manually.
 * PRSNL
 * OpenAPI spec version: 6.0.0-beta.2
 */
import type { DevelopmentStatsByLanguage } from './developmentStatsByLanguage';
import type { DevelopmentStatsByCategory } from './developmentStatsByCategory';
import type { DevelopmentStatsByDifficulty } from './developmentStatsByDifficulty';
import type { DevelopmentStatsRecentActivityItem } from './developmentStatsRecentActivityItem';

export interface DevelopmentStats {
  total_items: number;
  by_language: DevelopmentStatsByLanguage;
  by_category: DevelopmentStatsByCategory;
  by_difficulty: DevelopmentStatsByDifficulty;
  career_related_count: number;
  recent_activity: DevelopmentStatsRecentActivityItem[];
}
