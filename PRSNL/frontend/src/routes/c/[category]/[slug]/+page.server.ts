import { error, redirect } from '@sveltejs/kit';
import type { PageServerLoad } from './$types';
import { getApiEndpoint, getServerApiUrl } from '$lib/utils/api-url';

const VALID_CATEGORIES = ['dev', 'learn', 'media', 'ideas'];

export const load: PageServerLoad = async ({ params, fetch, url }) => {
  const { category, slug } = params;

  // Validate category
  if (!VALID_CATEGORIES.includes(category)) {
    throw error(404, 'Category not found');
  }

  // Validate slug format
  if (!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(slug)) {
    throw error(404, 'Invalid URL format');
  }

  // Special handling for videos: redirect to video player to avoid massive content processing
  if (category === 'media') {
    try {
      const videoResolutionResponse = await fetch(
        getApiEndpoint(`/video-resolution/${category}/${slug}`)
      );

      if (videoResolutionResponse.ok) {
        const videoData = await videoResolutionResponse.json();
        if (videoData.videoId && videoData.videoUrl) {
          // Redirect to video player route which handles videos properly
          throw redirect(302, videoData.videoUrl);
        }
      }
    } catch (redirectError) {
      // If it's a redirect, re-throw it
      if (
        redirectError &&
        typeof redirectError === 'object' &&
        'status' in redirectError &&
        redirectError.status === 302
      ) {
        throw redirectError;
      }
      // If video resolution fails, continue with normal content loading as fallback
      console.log('Video resolution failed, falling back to content route');
    }
  }

  try {
    // Fetch content by category and slug
    // Use the provided fetch function which handles SSR properly
    const response = await fetch(getApiEndpoint(`/content/${category}/${slug}`));

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
    // If it's already a SvelteKit error, re-throw it
    if (err && typeof err === 'object' && 'status' in err && 'body' in err) {
      throw err;
    }
    // Otherwise, log and throw a generic error
    console.error('Error loading content:', err);
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
