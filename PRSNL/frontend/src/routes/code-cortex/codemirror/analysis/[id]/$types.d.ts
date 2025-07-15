import type { PageServerLoad } from '@sveltejs/kit';

export type PageData = {
	analysisId: string;
	analysis: {
		id: string;
		repository_name?: string;
		created_at: string;
		analysis_depth?: string;
		analysis_type?: string;
		security_score?: number;
		performance_score?: number;
		quality_score?: number;
		file_count?: number;
		languages_detected?: string[] | string;
		frameworks_detected?: string[] | string;
		results?: any;
	};
	insights: Array<{
		id: string;
		title: string;
		description: string;
		severity?: string;
		recommendation?: string;
		confidence_score?: number;
		insight_type: string;
	}>;
	knowledgeContent: {
		total_results: number;
		search_terms_used?: string[];
		videos?: any[];
		photos?: any[];
		documents?: any[];
		notes?: any[];
		open_source_integrations?: any[];
		chatgpt_conversations?: any[];
	} | null;
	languages: string[];
	frameworks: string[];
	fileCount: number;
	parsedResults: any;
};

export { PageServerLoad };