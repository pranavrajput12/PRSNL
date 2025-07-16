import { error } from '@sveltejs/kit';
import type { PageServerLoad } from './$types';
import { getApiEndpoint } from '$lib/utils/api-url';

const VALID_CATEGORIES = ['dev', 'learn', 'media', 'ideas'];

export const load: PageServerLoad = async ({ params, url, fetch }) => {
  const { category } = params;

  // Validate category
  if (!VALID_CATEGORIES.includes(category)) {
    throw error(404, 'Category not found');
  }

  // Get query parameters
  const page = Number(url.searchParams.get('page')) || 1;
  const limit = Number(url.searchParams.get('limit')) || 20;
  const sort = url.searchParams.get('sort') || 'recent';
  const search = url.searchParams.get('search') || '';

  try {
    // Build query parameters
    const queryParams = new URLSearchParams({
      page: page.toString(),
      limit: limit.toString(),
      sort,
      ...(search && { search }),
    });

    // Fetch content by category using the new API endpoint
    const response = await fetch(
      getApiEndpoint(`/content/category/${category}?${queryParams}`)
    );

    if (!response.ok) {
      if (response.status === 404) {
        throw error(404, 'Category not found');
      }
      throw error(500, 'Failed to load category content');
    }

    const data = await response.json();

    return {
      category,
      categoryInfo: getCategoryInfo(category),
      content: data.content || [],
      pagination: data.pagination || {
        page: 1,
        totalPages: 1,
        total: 0,
        hasNext: false,
        hasPrev: false,
      },
      filters: {
        sort,
        search,
        page,
      },
    };
  } catch (err) {
    if (err instanceof Error && 'status' in err) {
      throw err; // Re-throw SvelteKit errors
    }
    console.error('Failed to load category content:', err);
    throw error(500, 'Failed to load category content');
  }
};

function getCategoryInfo(category: string) {
  const categoryData = {
    dev: {
      title: 'Development',
      description: 'Programming resources, repositories, documentation, and development tools',
      color: '#00ff88',
      icon: 'code',
    },
    learn: {
      title: 'Learning',
      description: 'Tutorials, courses, articles, and educational content',
      color: '#4a9eff',
      icon: 'book',
    },
    media: {
      title: 'Media',
      description: 'Videos, images, audio content, and presentations',
      color: '#f59e0b',
      icon: 'play',
    },
    ideas: {
      title: 'Ideas',
      description: 'Personal notes, thoughts, reflections, and bookmarks',
      color: '#dc143c',
      icon: 'lightbulb',
    },
  };

  return categoryData[category] || categoryData.ideas;
}

function generateBreadcrumbs(category: string) {
  const categoryInfo = getCategoryInfo(category);

  return [
    { label: 'Home', href: '/' },
    { label: 'Content', href: '/c' },
    { label: categoryInfo.title, href: `/c/${category}`, active: true },
  ];
}
