import { error, redirect } from '@sveltejs/kit';
import type { PageServerLoad } from './$types';

const VALID_PAGES = ['import', 'settings', 'docs', 'health'];

// Legacy page mappings
const PAGE_REDIRECTS = {
  'import/v1': 'import',
  'import/v2': 'import',
};

export const load: PageServerLoad = async ({ params, url }) => {
  let { page } = params;

  // Handle legacy redirects
  if (PAGE_REDIRECTS[page]) {
    const redirectPath = PAGE_REDIRECTS[page];
    // Preserve query parameters for import variants
    const queryString = url.search;
    throw redirect(301, `/s/${redirectPath}${queryString}`);
  }

  // Validate page
  if (!VALID_PAGES.includes(page)) {
    throw error(404, 'System page not found');
  }

  // Page configuration
  const pageConfig = getPageConfig(page);

  // Special handling for import page variants
  let importVariant = null;
  if (page === 'import') {
    const variant = url.searchParams.get('v') || url.pathname.includes('/v2') ? 'v2' : 'v1';
    importVariant = variant;
  }

  return {
    page,
    pageConfig,
    importVariant,
    breadcrumbs: generateBreadcrumbs(page, pageConfig.title),
  };
};

function getPageConfig(page: string) {
  const pages = {
    import: {
      title: 'Knowledge Sync',
      description: 'Import and synchronize external data sources',
      icon: 'download',
      color: '#4a9eff',
      legacyPath: '/import',
    },
    settings: {
      title: 'Settings',
      description: 'System configuration and preferences',
      icon: 'settings',
      color: '#00ff88',
      legacyPath: '/settings',
    },
    docs: {
      title: 'Documentation',
      description: 'System documentation and help resources',
      icon: 'help-circle',
      color: '#f59e0b',
      legacyPath: '/docs',
    },
    health: {
      title: 'System Health',
      description: 'Monitor system status and performance',
      icon: 'activity',
      color: '#dc143c',
      legacyPath: '/health',
    },
  };

  return pages[page] || pages.settings;
}

function generateBreadcrumbs(page: string, title: string) {
  return [
    { label: 'Home', href: '/' },
    { label: 'System', href: '/s' },
    { label: title, href: `/s/${page}`, active: true },
  ];
}
