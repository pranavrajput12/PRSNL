import { error, redirect } from '@sveltejs/kit';
import type { PageServerLoad } from './$types';

const VALID_TOOLS = ['timeline', 'insights', 'chat', 'visual', 'code'];

// Legacy tool mappings
const TOOL_REDIRECTS = {
  'code-cortex': 'code',
  videos: 'visual',
};

export const load: PageServerLoad = async ({ params }) => {
  let { tool } = params;

  // Handle legacy redirects
  if (TOOL_REDIRECTS[tool]) {
    throw redirect(301, `/p/${TOOL_REDIRECTS[tool]}`);
  }

  // Validate tool
  if (!VALID_TOOLS.includes(tool)) {
    throw error(404, 'Tool not found');
  }

  // Tool configuration
  const toolConfig = getToolConfig(tool);

  return {
    tool,
    toolConfig,
    breadcrumbs: generateBreadcrumbs(tool, toolConfig.title),
  };
};

function getToolConfig(tool: string) {
  const tools = {
    timeline: {
      title: 'Timeline',
      description: 'Chronological view of your content stream',
      icon: 'clock',
      color: '#4a9eff',
      legacyPath: '/timeline',
    },
    insights: {
      title: 'Insights',
      description: 'AI-powered analytics and content discovery',
      icon: 'trending-up',
      color: '#00ff88',
      legacyPath: '/insights',
    },
    chat: {
      title: 'Mind Palace',
      description: 'Conversational AI interface for your knowledge',
      icon: 'message-circle',
      color: '#f59e0b',
      legacyPath: '/chat',
    },
    visual: {
      title: 'Visual Cortex',
      description: 'Video and media content center',
      icon: 'play',
      color: '#dc143c',
      legacyPath: '/videos',
    },
    code: {
      title: 'Code Cortex',
      description: 'Development content and project hub',
      icon: 'terminal',
      color: '#9333ea',
      legacyPath: '/code-cortex',
    },
  };

  return tools[tool] || tools.timeline;
}

function generateBreadcrumbs(tool: string, title: string) {
  return [
    { label: 'Home', href: '/' },
    { label: 'Processing', href: '/p' },
    { label: title, href: `/p/${tool}`, active: true },
  ];
}
