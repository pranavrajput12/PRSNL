import { error } from '@sveltejs/kit';
import type { PageServerLoad } from './$types';

const VALID_CATEGORIES = ['dev', 'learn', 'media', 'ideas'];

export const load: PageServerLoad = async ({ params, fetch }) => {
  const { category, slug } = params;

  // Validate category
  if (!VALID_CATEGORIES.includes(category)) {
    throw error(404, 'Category not found');
  }

  // Validate slug format
  if (!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(slug)) {
    throw error(404, 'Invalid URL format');
  }

  try {
    // Fetch content by category and slug
    const response = await fetch(`http://localhost:8000/api/content/${category}/${slug}`);

    if (!response.ok) {
      if (response.status === 404) {
        throw error(404, 'Content not found');
      }
      throw error(500, 'Failed to load content');
    }

    const data = await response.json();

    return {
      content: data.content,
      contentUrl: data.contentUrl,
      relatedContent: data.relatedContent || [],
      breadcrumbs: generateBreadcrumbs(category, slug, data.content.title),
      seo: generateSEOData(data.content, category, slug),
    };
  } catch (err) {
    if (err instanceof Error && 'status' in err) {
      throw err; // Re-throw SvelteKit errors
    }
    throw error(500, 'Failed to load content');
  }
};

function generateBreadcrumbs(category: string, slug: string, title: string) {
  const categoryLabels = {
    dev: 'Development',
    learn: 'Learning',
    media: 'Media',
    ideas: 'Ideas',
  };

  return [
    { label: 'Home', href: '/' },
    { label: 'Content', href: '/c' },
    { label: categoryLabels[category] || category, href: `/c/${category}` },
    { label: title, href: `/c/${category}/${slug}`, active: true },
  ];
}

function generateSEOData(content: any, category: string, slug: string) {
  return {
    title: `${content.title} | PRSNL`,
    description: content.summary || content.meta_description || `${content.title} - PRSNL content`,
    canonical: `/c/${category}/${slug}`,
    type: getOpenGraphType(category),
    image: content.thumbnail_url || content.preview_image,
  };
}

function getOpenGraphType(category: string): string {
  switch (category) {
    case 'media':
      return 'video.other';
    case 'learn':
      return 'article';
    default:
      return 'website';
  }
}
