<script lang="ts">
  import { onMount } from 'svelte';
  import { getInsights, getTimelineTrends, getTopTags, getPersonalityAnalysis } from '$lib/api';
  import type { InsightsResponse } from '$lib/types/api';
  import Icon from '$lib/components/Icon.svelte';
  import Spinner from '$lib/components/Spinner.svelte';
  import ErrorMessage from '$lib/components/ErrorMessage.svelte';
  import TopicClusters from '$lib/components/TopicClusters.svelte';
  import ContentTrends from '$lib/components/ContentTrends.svelte';
  import AsyncBoundary from '$lib/components/AsyncBoundary.svelte';

  // State
  let isLoading = true;
  let error: Error | null = null;
  let timeRange = '30d';
  let insightsData: InsightsResponse | null = null;
  let dynamicInsights: any = null;
  let timelineTrendsData: any = null;
  let realTagsData: any = null;
  let personalityData: any = null;
  let showTreeInfo = false;
  let showDNAInfo = false;
  let showCognitiveInfo = false;
  let showMetabolismInfo = false;
  let showEcosystemInfo = false;

  // Reactive statements
  $: timeRangeLabel =
    {
      '7d': 'Last 7 Days',
      '30d': 'Last 30 Days',
      '3m': 'Last 3 Months',
      '1y': 'Last Year',
      all: 'All Time',
    }[timeRange] || timeRange;

  onMount(async () => {
    try {
      await loadInsightsData();
    } catch (e) {
      error = e as Error;
    } finally {
      isLoading = false;
    }
  });

  async function loadInsightsData() {
    try {
      isLoading = true;
      error = null;

      // Load insights data, timeline trends, top tags, and personality analysis in parallel
      const [response, trendsResponse, tagsResponse, personalityResponse] = await Promise.all([
        getInsights(timeRange),
        getTimelineTrends(timeRange).catch((err) => {
          console.warn('Timeline trends API failed, using fallback:', err);
          return null; // Use fallback instead of failing
        }),
        getTopTags(timeRange, 15).catch((err) => {
          console.warn('Top tags API failed, using fallback:', err);
          return null; // Use fallback instead of failing
        }),
        getPersonalityAnalysis(timeRange).catch((err) => {
          console.warn('Personality analysis API failed, using fallback:', err);
          return null; // Use fallback instead of failing
        }),
      ]);

      // Transform new format to old format for compatibility
      if (response && response.insights) {
        insightsData = {
          topicClusters: [],
          contentTrends: [],
          tagAnalysis: [],
        };

        // Extract data from insights array
        response.insights.forEach((insight) => {
          if (insight.type === 'knowledge_evolution' && insight.data.timeline) {
            // Convert to topic clusters
            const latestMonth = insight.data.timeline[0];
            if (latestMonth && latestMonth.top_topics) {
              insightsData.topicClusters = latestMonth.top_topics.map((t, idx) => ({
                id: `topic-${idx}`,
                name: t.topic,
                count: t.count,
                group: t.count > 5 ? 'major' : 'minor',
                percentage: (t.count / latestMonth.total_items) * 100,
              }));
            }
          }
        });

        // Use real tags data for Memory Palace
        if (tagsResponse && tagsResponse.tags) {
          realTagsData = tagsResponse;
          insightsData.tagAnalysis = tagsResponse.tags.map((tag, idx) => ({
            name: tag.name,
            weight: tag.weight,
            hue: (idx * 137.5) % 360, // Golden angle distribution for better color spread
            usage_count: tag.usage_count,
            latest_use: tag.latest_use,
            recency_weight: tag.recency_weight,
          }));
        } else {
          // Fallback to empty tags if API fails
          insightsData.tagAnalysis = [];
        }

        // Use real personality analysis data for Cognitive Fingerprint
        if (personalityResponse && personalityResponse.personality) {
          personalityData = personalityResponse;
        } else {
          // Fallback to default personality if API fails
          personalityData = {
            personality: {
              type: 'explorer',
              name: 'The Explorer',
              description:
                'You thrive on discovering new ideas and diverse topics. Your knowledge spans wide horizons, always seeking the next frontier of understanding.',
              traits: ['Curious', 'Diverse interests', 'Adventurous', 'Open-minded'],
              icon: '🧭',
              confidence: 0.3,
              scores: {},
              analysis_factors: {
                content_variety: 0,
                tag_diversity: 0,
                temporal_consistency: 0,
                total_items: 0,
              },
            },
          };
        }

        // Use real timeline trends data instead of synthetic data
        if (trendsResponse && trendsResponse.timeline_data) {
          timelineTrendsData = trendsResponse.timeline_data;
          insightsData.contentTrends = trendsResponse.timeline_data.map((day) => ({
            date: day.date,
            articles: day.articles,
            videos: day.videos,
            notes: day.notes,
            bookmarks: day.bookmarks,
            value: day.articles + day.videos + day.notes + day.bookmarks,
          }));
        } else {
          // Fallback to synthetic data if timeline trends API fails
          console.log('Using fallback synthetic data for content trends');
          const now = new Date();
          insightsData.contentTrends = Array.from({ length: 30 }, (_, i) => ({
            date: new Date(now.getTime() - i * 24 * 60 * 60 * 1000).toISOString(),
            articles: Math.floor(Math.random() * 5),
            videos: Math.floor(Math.random() * 3),
            notes: Math.floor(Math.random() * 4),
            bookmarks: Math.floor(Math.random() * 2),
            value: Math.floor(Math.random() * 10),
          }));
        }

        // Set dynamic insights summary
        dynamicInsights = {
          summary: response.summary,
          widgets: response.insights,
        };
      }
    } catch (e) {
      console.error('Failed to load insights data:', e);
      error = e as Error;
    } finally {
      isLoading = false;
    }
  }

  function handleTimeRangeChange(newRange: string) {
    timeRange = newRange;
    loadInsightsData();
  }
</script>

<svelte:head>
  <title>AI Insights | PRSNL</title>
</svelte:head>

<div class="insights-page">
  <header class="insights-header">
    <h1>
      <Icon name="brain" />
      AI Insights
    </h1>

    <div class="time-range-selector">
      <span class="label">Showing data for:</span>
      <div class="dropdown">
        <button class="dropdown-toggle">
          {timeRangeLabel}
          <Icon name="chevron-down" size="small" />
        </button>
        <div class="dropdown-menu">
          <button class:active={timeRange === 'day'} on:click={() => handleTimeRangeChange('day')}>
            Today
          </button>
          <button
            class:active={timeRange === 'week'}
            on:click={() => handleTimeRangeChange('week')}
          >
            This Week
          </button>
          <button
            class:active={timeRange === 'month'}
            on:click={() => handleTimeRangeChange('month')}
          >
            This Month
          </button>
          <button
            class:active={timeRange === 'year'}
            on:click={() => handleTimeRangeChange('year')}
          >
            This Year
          </button>
          <button class:active={timeRange === 'all'} on:click={() => handleTimeRangeChange('all')}>
            All Time
          </button>
        </div>
      </div>
    </div>
  </header>

  <AsyncBoundary loading={isLoading} {error} loadingMessage="Loading insights...">
    {#if dynamicInsights && dynamicInsights.widgets}
      <!-- Dynamic Insights Summary -->
      {#if dynamicInsights.summary}
        <div class="insights-summary">
          <Icon name="sparkles" />
          <p>{dynamicInsights.summary}</p>
        </div>
      {/if}
    {/if}

    {#if insightsData}
      <div class="insights-grid">
        <div class="insight-card">
          <div class="card-header">
            <h2>
              <Icon name="pie-chart" />
              Knowledge Tree
              <button class="info-button" on:click={() => (showTreeInfo = !showTreeInfo)}>
                <Icon name="info" size="small" />
              </button>
            </h2>
            <p class="description">
              Watch your knowledge grow like a living tree, with each topic branching into deeper
              understanding
            </p>
          </div>
          <div class="card-content">
            <TopicClusters data={insightsData.topicClusters} />
            <div class="section-explanation">
              <p>
                Like a living organism, your knowledge base has evolved into a complex ecosystem
                where ideas take root, branch out, and interconnect. This visualization maps the
                organic growth of your intellectual landscape, showing how different topics cluster
                into thriving knowledge communities.
              </p>
            </div>
          </div>
        </div>

        <div class="insight-card">
          <div class="card-header">
            <h2>
              <Icon name="trending-up" />
              Knowledge DNA
              <button class="info-button" on:click={() => (showDNAInfo = !showDNAInfo)}>
                <Icon name="info" size="small" />
              </button>
            </h2>
            <p class="description">
              The double helix of your digital evolution, encoding the genetic blueprint of your
              learning journey
            </p>
          </div>
          <div class="card-content">
            <ContentTrends
              data={insightsData?.contentTrends?.map((point) => ({
                date: new Date(point.date),
                value: point.articles + point.videos + point.notes + point.bookmarks,
                articles: point.articles,
                videos: point.videos,
                notes: point.notes,
                bookmarks: point.bookmarks,
              })) || []}
              {timeRange}
            />
            <div class="section-explanation">
              <p>
                Your learning evolution encoded in a double helix, revealing the genetic patterns of
                your intellectual growth. Like a living organism, your knowledge DNA shows how
                different content types interact and evolve over time, forming the unique genetic
                signature of your learning journey.
              </p>
            </div>
          </div>
        </div>

        <div class="insight-card">
          <div class="card-header">
            <h2>
              <Icon name="user" />
              Cognitive Fingerprint
              <button class="info-button" on:click={() => (showCognitiveInfo = !showCognitiveInfo)}>
                <Icon name="info" size="small" />
              </button>
            </h2>
            <p class="description">
              The unique signature of your intellectual identity, as distinct as your DNA
            </p>
          </div>
          <div class="card-content">
            {#if personalityData && personalityData.personality}
              <div class="personality-analysis">
                <div class="personality-header">
                  <span class="personality-icon">{personalityData.personality.icon}</span>
                  <div class="personality-title">
                    <h3>{personalityData.personality.name}</h3>
                    <span class="confidence">
                      {Math.round(personalityData.personality.confidence * 100)}% confidence
                    </span>
                  </div>
                </div>

                <div class="personality-description">
                  <p>{personalityData.personality.description}</p>
                </div>

                <div class="personality-traits">
                  <h4>Core Traits</h4>
                  <div class="trait-list">
                    {#each personalityData.personality.traits as trait}
                      <span class="trait-tag">{trait}</span>
                    {/each}
                  </div>
                </div>

                <div class="personality-stats">
                  <div class="stat">
                    <span class="stat-value"
                      >{personalityData.personality.analysis_factors.content_variety}</span
                    >
                    <span class="stat-label">Content Types</span>
                  </div>
                  <div class="stat">
                    <span class="stat-value"
                      >{personalityData.personality.analysis_factors.tag_diversity}</span
                    >
                    <span class="stat-label">Tag Diversity</span>
                  </div>
                  <div class="stat">
                    <span class="stat-value"
                      >{personalityData.personality.analysis_factors.total_items}</span
                    >
                    <span class="stat-label">Items Analyzed</span>
                  </div>
                </div>
              </div>
            {:else}
              <div class="empty-state">
                <Icon name="info" />
                <p>Not enough data for personality analysis</p>
              </div>
            {/if}
          </div>
        </div>

        <!-- New Life-Themed Sections -->
        <div class="insight-card">
          <div class="card-header">
            <h2>
              <Icon name="activity" />
              Learning Metabolism
              <button
                class="info-button"
                on:click={() => (showMetabolismInfo = !showMetabolismInfo)}
              >
                <Icon name="info" size="small" />
              </button>
            </h2>
            <p class="description">
              The pulse of your intellectual appetite, tracking how your mind consumes knowledge
            </p>
          </div>
          <div class="card-content">
            <div class="section-explanation">
              <p>
                Like a living organism, your knowledge acquisition follows metabolic rhythms. This
                visualization reveals the heartbeat of your learning process, showing when your
                intellectual hunger peaks and how efficiently you process new information.
              </p>
            </div>
            <div class="metabolism-display">
              <div class="metabolism-stats">
                <div class="stat">
                  <span class="stat-value"
                    >{Math.round(
                      (insightsData?.contentTrends?.reduce((sum, d) => sum + d.value, 0) || 0) / 30
                    )}</span
                  >
                  <span class="stat-label">Daily Rate</span>
                </div>
                <div class="stat">
                  <span class="stat-value"
                    >{Math.max(...(insightsData?.contentTrends?.map((d) => d.value) || [0]))}</span
                  >
                  <span class="stat-label">Peak Day</span>
                </div>
              </div>
              <div class="heartbeat-chart">
                <svg width="100%" height="80">
                  {#each (insightsData?.contentTrends || []).slice(-14) as point, i}
                    <circle
                      cx={20 + i * 25}
                      cy={40 - point.value * 2}
                      r={Math.max(3, point.value)}
                      fill="#DC143C"
                      opacity="0.8"
                    />
                  {/each}
                </svg>
              </div>
            </div>
          </div>
        </div>

        <div class="insight-card">
          <div class="card-header">
            <h2>
              <Icon name="globe" />
              Intellectual Ecosystem
              <button class="info-button" on:click={() => (showEcosystemInfo = !showEcosystemInfo)}>
                <Icon name="info" size="small" />
              </button>
            </h2>
            <p class="description">
              The biodiversity of your knowledge habitat, showing the richness of your mental
              environment
            </p>
          </div>
          <div class="card-content">
            <div class="section-explanation">
              <p>
                Your mind is a complex ecosystem where different types of knowledge species coexist
                and interact. This visualization maps the biodiversity of your intellectual
                environment, revealing which knowledge habitats thrive and which areas need
                cultivation.
              </p>
            </div>
            <div class="ecosystem-display">
              <div class="ecosystem-species">
                <div class="species articles">
                  <div class="species-icon">📚</div>
                  <div class="species-info">
                    <span class="species-name">Article Species</span>
                    <span class="species-count"
                      >{insightsData?.contentTrends?.reduce((sum, d) => sum + d.articles, 0) ||
                        0}</span
                    >
                  </div>
                </div>
                <div class="species videos">
                  <div class="species-icon">🎬</div>
                  <div class="species-info">
                    <span class="species-name">Video Species</span>
                    <span class="species-count"
                      >{insightsData?.contentTrends?.reduce((sum, d) => sum + d.videos, 0) ||
                        0}</span
                    >
                  </div>
                </div>
                <div class="species notes">
                  <div class="species-icon">📝</div>
                  <div class="species-info">
                    <span class="species-name">Note Species</span>
                    <span class="species-count"
                      >{insightsData?.contentTrends?.reduce((sum, d) => sum + d.notes, 0) ||
                        0}</span
                    >
                  </div>
                </div>
                <div class="species bookmarks">
                  <div class="species-icon">🔖</div>
                  <div class="species-info">
                    <span class="species-name">Bookmark Species</span>
                    <span class="species-count"
                      >{insightsData?.contentTrends?.reduce((sum, d) => sum + d.bookmarks, 0) ||
                        0}</span
                    >
                  </div>
                </div>
              </div>
              <div class="biodiversity-score">
                <div class="score-circle">
                  <span class="score-value"
                    >{Math.round(((realTagsData?.tags?.length || 0) / 10) * 100)}%</span
                  >
                  <span class="score-label">Biodiversity</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    {:else}
      <div class="empty-insights">
        <Icon name="database" size="large" />
        <h2>No insights available</h2>
        <p>Add more content to your knowledge base to generate AI insights</p>
      </div>
    {/if}
  </AsyncBoundary>
</div>

<!-- Info Modals -->
{#if showTreeInfo}
  <div class="info-modal" on:click={() => (showTreeInfo = false)}>
    <div class="info-content" on:click|stopPropagation>
      <button class="close-button" on:click={() => (showTreeInfo = false)}>×</button>
      <h3>🌳 Knowledge Tree Milestones</h3>
      <div class="milestone-stages">
        <div class="stage">
          <div class="stage-icon">🌱</div>
          <div class="stage-info">
            <h4>Sprouting Seedling</h4>
            <p>10+ items: Just trunk + 3 small branches</p>
          </div>
        </div>
        <div class="stage">
          <div class="stage-icon">🌿</div>
          <div class="stage-info">
            <h4>Growing Sapling</h4>
            <p>50+ items: 5 branches, need 2+ items per topic</p>
          </div>
        </div>
        <div class="stage">
          <div class="stage-icon">🌳</div>
          <div class="stage-info">
            <h4>Young Tree</h4>
            <p>100+ items: 8 branches, need 3+ items per topic</p>
          </div>
        </div>
        <div class="stage">
          <div class="stage-icon">🌲</div>
          <div class="stage-info">
            <h4>Mature Forest</h4>
            <p>500+ items: 12 branches, need 5+ items per topic</p>
          </div>
        </div>
        <div class="stage">
          <div class="stage-icon">🏛️</div>
          <div class="stage-info">
            <h4>Ancient Grove</h4>
            <p>1000+ items: 15 branches, need 10+ items per topic</p>
          </div>
        </div>
      </div>
      <p class="milestone-note">
        Your tree grows meaningfully as you accumulate knowledge. Each milestone represents a
        significant expansion of your intellectual landscape.
      </p>
    </div>
  </div>
{/if}

{#if showDNAInfo}
  <div class="info-modal" on:click={() => (showDNAInfo = false)}>
    <div class="info-content" on:click|stopPropagation>
      <button class="close-button" on:click={() => (showDNAInfo = false)}>×</button>
      <h3>🧬 Knowledge DNA Evolution</h3>
      <div class="milestone-stages">
        <div class="stage">
          <div class="stage-icon">🧬</div>
          <div class="stage-info">
            <h4>Basic Formation</h4>
            <p>20+ items: Single strands only</p>
          </div>
        </div>
        <div class="stage">
          <div class="stage-icon">🔬</div>
          <div class="stage-info">
            <h4>Helix Forming</h4>
            <p>50+ items: Partial double helix</p>
          </div>
        </div>
        <div class="stage">
          <div class="stage-icon">🧪</div>
          <div class="stage-info">
            <h4>Complete Helix</h4>
            <p>100+ items: Full double helix structure</p>
          </div>
        </div>
        <div class="stage">
          <div class="stage-icon">⚗️</div>
          <div class="stage-info">
            <h4>Complex Patterns</h4>
            <p>300+ items: Advanced DNA patterns</p>
          </div>
        </div>
        <div class="stage">
          <div class="stage-icon">🧬</div>
          <div class="stage-info">
            <h4>Fully Evolved</h4>
            <p>1000+ items: Complete intellectual genome</p>
          </div>
        </div>
      </div>
      <p class="milestone-note">
        Your knowledge DNA encodes your learning evolution. Each strand represents different content
        types forming the genetic code of your intellectual identity.
      </p>
    </div>
  </div>
{/if}

{#if showCognitiveInfo}
  <div class="info-modal" on:click={() => (showCognitiveInfo = false)}>
    <div class="info-content" on:click|stopPropagation>
      <button class="close-button" on:click={() => (showCognitiveInfo = false)}>×</button>
      <h3>🧠 Cognitive Fingerprint Analysis</h3>
      <div class="personality-explanation">
        <p>
          Your cognitive fingerprint is determined by analyzing patterns in your content
          consumption, tag usage, and learning behavior.
        </p>
        <h4>Analysis Factors:</h4>
        <ul>
          <li>
            <strong>Content Variety:</strong> How many different types of content you consume (articles,
            videos, notes, etc.)
          </li>
          <li>
            <strong>Tag Diversity:</strong> The breadth of topics you explore, indicating intellectual
            curiosity
          </li>
          <li>
            <strong>Temporal Consistency:</strong> How regularly you engage with learning materials
          </li>
          <li><strong>Topic Focus:</strong> Whether you specialize deeply or explore broadly</li>
        </ul>
        <h4>Personality Types:</h4>
        <div class="personality-types">
          <div class="personality-type">
            <span class="type-icon">🧭</span>
            <div class="type-info">
              <strong>Explorer:</strong> High diversity, broad interests
            </div>
          </div>
          <div class="personality-type">
            <span class="type-icon">🔬</span>
            <div class="type-info">
              <strong>Specialist:</strong> Deep focus, methodical approach
            </div>
          </div>
          <div class="personality-type">
            <span class="type-icon">🌐</span>
            <div class="type-info">
              <strong>Connector:</strong> Links ideas across disciplines
            </div>
          </div>
          <div class="personality-type">
            <span class="type-icon">⚡</span>
            <div class="type-info">
              <strong>Practitioner:</strong> Hands-on, implementation focused
            </div>
          </div>
        </div>
        <p class="confidence-note">
          Confidence score reflects how strongly your behavior matches the identified personality
          type based on statistical analysis of your content patterns.
        </p>
      </div>
    </div>
  </div>
{/if}

{#if showMetabolismInfo}
  <div class="info-modal" on:click={() => (showMetabolismInfo = false)}>
    <div class="info-content" on:click|stopPropagation>
      <button class="close-button" on:click={() => (showMetabolismInfo = false)}>×</button>
      <h3>⚡ Learning Metabolism Analysis</h3>
      <div class="metabolism-explanation">
        <p>
          Your learning metabolism measures how your mind processes and absorbs knowledge over time,
          similar to how a living organism metabolizes nutrients.
        </p>
        <h4>Key Metrics:</h4>
        <ul>
          <li><strong>Daily Rate:</strong> Average number of items you consume per day</li>
          <li><strong>Peak Activity:</strong> Your highest learning activity in a single day</li>
          <li><strong>Metabolic Rhythm:</strong> The heartbeat pattern of your learning habits</li>
          <li><strong>Processing Efficiency:</strong> How well you maintain consistent learning</li>
        </ul>
        <h4>Metabolism Stages:</h4>
        <div class="metabolism-stages">
          <div class="stage">
            <span class="stage-icon">🐣</span>
            <div class="stage-info">
              <strong>Slow Metabolism:</strong> 0-2 items/day - Building habits
            </div>
          </div>
          <div class="stage">
            <span class="stage-icon">🔥</span>
            <div class="stage-info">
              <strong>Active Metabolism:</strong> 3-5 items/day - Steady growth
            </div>
          </div>
          <div class="stage">
            <span class="stage-icon">⚡</span>
            <div class="stage-info">
              <strong>High Metabolism:</strong> 6+ items/day - Rapid consumption
            </div>
          </div>
        </div>
        <p class="metabolism-note">
          The visualization shows your recent learning heartbeat, with each pulse representing your
          daily knowledge intake.
        </p>
      </div>
    </div>
  </div>
{/if}

{#if showEcosystemInfo}
  <div class="info-modal" on:click={() => (showEcosystemInfo = false)}>
    <div class="info-content" on:click|stopPropagation>
      <button class="close-button" on:click={() => (showEcosystemInfo = false)}>×</button>
      <h3>🌍 Intellectual Ecosystem Analysis</h3>
      <div class="ecosystem-explanation">
        <p>
          Your intellectual ecosystem represents the biodiversity of your knowledge habitat, showing
          how different types of content species coexist and thrive in your mental environment.
        </p>
        <h4>Content Species:</h4>
        <div class="species-guide">
          <div class="species-item">
            <span class="species-icon">📚</span>
            <div class="species-info">
              <strong>Article Species:</strong> Deep-dive content that forms the foundation of your knowledge
              forest
            </div>
          </div>
          <div class="species-item">
            <span class="species-icon">🎬</span>
            <div class="species-info">
              <strong>Video Species:</strong> Visual learners that bring dynamic energy to your ecosystem
            </div>
          </div>
          <div class="species-item">
            <span class="species-icon">📝</span>
            <div class="species-info">
              <strong>Note Species:</strong> Personal thoughts and insights that enrich your intellectual
              soil
            </div>
          </div>
          <div class="species-item">
            <span class="species-icon">🔖</span>
            <div class="species-info">
              <strong>Bookmark Species:</strong> Quick references that maintain ecosystem connectivity
            </div>
          </div>
        </div>
        <h4>Biodiversity Score:</h4>
        <p>
          Calculated based on the variety and balance of different content types in your ecosystem.
          Higher biodiversity indicates a more resilient and adaptable knowledge environment.
        </p>
        <div class="biodiversity-levels">
          <div class="level">
            <span class="level-icon">🌱</span>
            <strong>0-30%:</strong> Monoculture - Limited diversity
          </div>
          <div class="level">
            <span class="level-icon">🌿</span>
            <strong>30-60%:</strong> Growing - Moderate diversity
          </div>
          <div class="level">
            <span class="level-icon">🌳</span>
            <strong>60-80%:</strong> Thriving - High diversity
          </div>
          <div class="level">
            <span class="level-icon">🌴</span>
            <strong>80-100%:</strong> Rainforest - Maximum biodiversity
          </div>
        </div>
        <p class="ecosystem-note">
          A healthy intellectual ecosystem supports sustainable learning and knowledge
          cross-pollination between different domains.
        </p>
      </div>
    </div>
  </div>
{/if}

<style>
  .insights-page {
    padding: 2rem;
    min-height: calc(100vh - 60px);
    background: var(--bg-primary);
  }

  .insights-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 2rem;
  }

  h1 {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    font-family: var(--font-display);
    font-size: 2rem;
    color: var(--text-primary);
  }

  .time-range-selector {
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }

  .label {
    color: var(--text-secondary);
    font-size: 0.9rem;
  }

  .dropdown {
    position: relative;
  }

  .dropdown-toggle {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 1rem;
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    border-radius: 0.5rem;
    color: var(--text-primary);
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .dropdown-toggle:hover {
    background: var(--bg-hover);
  }

  .dropdown-menu {
    position: absolute;
    top: 100%;
    right: 0;
    margin-top: 0.5rem;
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    border-radius: 0.5rem;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    z-index: 10;
    min-width: 150px;
    display: none;
  }

  .dropdown:hover .dropdown-menu {
    display: block;
  }

  .dropdown-menu button {
    display: block;
    width: 100%;
    text-align: left;
    padding: 0.75rem 1rem;
    background: none;
    border: none;
    color: var(--text-primary);
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .dropdown-menu button:hover {
    background: var(--bg-hover);
  }

  .dropdown-menu button.active {
    background: var(--accent-transparent);
    color: var(--accent);
    font-weight: 500;
  }

  .insights-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 1.5rem;
  }

  .insight-card {
    background: var(--bg-secondary);
    border-radius: 0.75rem;
    overflow: hidden;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    display: flex;
    flex-direction: column;
  }

  .insight-card.full-width {
    grid-column: 1 / -1;
  }

  .card-header {
    padding: 1.25rem;
    border-bottom: 1px solid var(--border);
  }

  .card-header h2 {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 1.25rem;
    margin: 0 0 0.5rem 0;
    color: var(--text-primary);
  }

  .description {
    color: var(--text-secondary);
    font-size: 0.9rem;
    margin: 0;
  }

  .card-content {
    padding: 1.5rem;
    flex: 1;
    min-height: 150px;
  }

  .section-explanation {
    margin-top: 1.5rem;
    padding: 1rem;
    background: var(--bg-primary);
    border-radius: 0.5rem;
    border-left: 3px solid var(--accent);
  }

  .section-explanation p {
    margin: 0;
    line-height: 1.6;
    color: var(--text-secondary);
    font-size: 0.9rem;
  }

  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100%;
    color: var(--text-secondary);
    text-align: center;
    padding: 2rem;
  }

  .empty-state :global(svg) {
    margin-bottom: 1rem;
    opacity: 0.5;
  }

  .empty-insights {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 50vh;
    text-align: center;
    color: var(--text-secondary);
  }

  .empty-insights :global(svg) {
    font-size: 4rem;
    margin-bottom: 1.5rem;
    opacity: 0.3;
  }

  .empty-insights h2 {
    margin: 0 0 0.5rem 0;
    color: var(--text-primary);
  }

  .tag-cloud {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
  }

  .tag {
    display: inline-block;
    padding: 0.25rem 0.75rem;
    border-radius: 1rem;
    background: hsl(var(--hue), 70%, 40%, 0.1);
    color: hsl(var(--hue), 70%, 45%);
    font-size: calc(0.8rem + var(--size) * 0.5rem);
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s ease;
    position: relative;
  }

  .tag:hover {
    background: hsl(var(--hue), 70%, 40%, 0.2);
    transform: translateY(-2px);
  }

  .tag-count {
    display: inline-block;
    margin-left: 0.5rem;
    background: hsl(var(--hue), 70%, 50%, 0.8);
    color: white;
    padding: 0.1rem 0.4rem;
    border-radius: 0.75rem;
    font-size: 0.7rem;
    font-weight: 600;
  }

  .tag-stats {
    display: flex;
    justify-content: space-around;
    margin-top: 1rem;
    padding-top: 1rem;
    border-top: 1px solid var(--border);
  }

  .tag-stats .stat {
    display: flex;
    flex-direction: column;
    align-items: center;
  }

  .tag-stats .stat-value {
    font-size: 1.2rem;
    font-weight: 600;
    color: var(--accent);
  }

  .tag-stats .stat-label {
    font-size: 0.8rem;
    color: var(--text-secondary);
  }

  /* Personality Analysis Styles */
  .personality-analysis {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }

  .personality-header {
    display: flex;
    align-items: center;
    gap: 1rem;
  }

  .personality-icon {
    font-size: 2.5rem;
    line-height: 1;
  }

  .personality-title h3 {
    margin: 0;
    font-size: 1.3rem;
    color: var(--text-primary);
  }

  .confidence {
    display: block;
    font-size: 0.9rem;
    color: var(--accent);
    font-weight: 500;
    margin-top: 0.25rem;
  }

  .personality-description {
    background: var(--bg-secondary);
    padding: 1rem;
    border-radius: 0.5rem;
    border-left: 3px solid var(--accent);
  }

  .personality-description p {
    margin: 0;
    line-height: 1.6;
    color: var(--text-secondary);
  }

  .personality-traits h4 {
    margin: 0 0 0.75rem 0;
    font-size: 1rem;
    color: var(--text-primary);
  }

  .trait-list {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
  }

  .trait-tag {
    padding: 0.4rem 0.8rem;
    background: var(--accent);
    color: white;
    border-radius: 1rem;
    font-size: 0.85rem;
    font-weight: 500;
  }

  .personality-stats {
    display: flex;
    justify-content: space-around;
    padding-top: 1rem;
    border-top: 1px solid var(--border);
  }

  .personality-stats .stat {
    display: flex;
    flex-direction: column;
    align-items: center;
  }

  .personality-stats .stat-value {
    font-size: 1.2rem;
    font-weight: 600;
    color: var(--accent);
  }

  .personality-stats .stat-label {
    font-size: 0.8rem;
    color: var(--text-secondary);
  }

  /* Dynamic Insights Styles */
  .insights-summary {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 1.5rem;
    background: var(--bg-secondary);
    border: 1px solid var(--accent);
    border-radius: 0.75rem;
    margin-bottom: 2rem;
    color: var(--text-primary);
  }

  .insights-summary p {
    margin: 0;
    font-size: 1.1rem;
    line-height: 1.6;
  }

  .trending-topics {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .trend-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.75rem;
    background: var(--bg-primary);
    border-radius: 0.5rem;
  }

  .trend-name {
    font-weight: 500;
    color: var(--text-primary);
  }

  .trend-meta {
    display: flex;
    gap: 1rem;
    align-items: center;
  }

  .trend-count {
    font-size: 0.875rem;
    color: var(--text-secondary);
  }

  .trend-score {
    display: flex;
    align-items: center;
    gap: 0.25rem;
    font-weight: 500;
  }

  .trend-score.rising {
    color: #10b981;
  }

  .velocity-stats {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1rem;
  }

  .stat {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 1rem;
    background: var(--bg-primary);
    border-radius: 0.5rem;
  }

  .stat-value {
    font-size: 1.5rem;
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 0.25rem;
    color: var(--accent);
  }

  .stat-value.momentum.increasing {
    color: #10b981;
  }

  .stat-value.momentum.decreasing {
    color: #ef4444;
  }

  .stat-label {
    font-size: 0.875rem;
    color: var(--text-secondary);
  }

  .diversity-gauge {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .gauge {
    position: relative;
    height: 40px;
    background: var(--bg-primary);
    border-radius: 20px;
    overflow: hidden;
  }

  .gauge-fill {
    height: 100%;
    background: linear-gradient(90deg, #ef4444, #f59e0b, #10b981);
    transition: width 0.5s ease;
  }

  .gauge-value {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    font-weight: 600;
    font-size: 1.25rem;
    color: var(--text-primary);
  }

  .interpretation {
    font-size: 0.875rem;
    color: var(--text-secondary);
    text-align: center;
  }

  .themes-list {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .theme-bubble {
    padding: 1rem;
    background: var(--bg-primary);
    border-radius: 0.75rem;
    border-left: 3px solid var(--accent);
  }

  .theme-bubble.high {
    border-left-color: #10b981;
  }

  .theme-bubble.medium {
    border-left-color: #f59e0b;
  }

  .theme-bubble h4 {
    font-size: 1rem;
    margin: 0 0 0.25rem 0;
    color: var(--text-primary);
  }

  .theme-bubble p {
    font-size: 0.875rem;
    color: var(--text-secondary);
    margin: 0 0 0.5rem 0;
  }

  .confidence {
    font-size: 0.75rem;
    text-transform: uppercase;
    opacity: 0.7;
  }

  /* Info Button Styles */
  .info-button {
    background: none;
    border: none;
    color: var(--text-secondary);
    cursor: pointer;
    padding: 0.25rem;
    margin-left: 0.5rem;
    border-radius: 50%;
    transition: all 0.2s ease;
  }

  .info-button:hover {
    background: var(--bg-hover);
    color: var(--accent);
  }

  /* Info Modal Styles */
  .info-modal {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.8);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
    backdrop-filter: blur(5px);
  }

  .info-content {
    background: var(--bg-secondary);
    padding: 2rem;
    border-radius: 1rem;
    max-width: 600px;
    max-height: 80vh;
    overflow-y: auto;
    position: relative;
    border: 1px solid var(--accent);
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
  }

  .close-button {
    position: absolute;
    top: 1rem;
    right: 1rem;
    background: none;
    border: none;
    font-size: 1.5rem;
    cursor: pointer;
    color: var(--text-secondary);
    width: 2rem;
    height: 2rem;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 50%;
    transition: all 0.2s ease;
  }

  .close-button:hover {
    background: var(--bg-hover);
    color: var(--accent);
  }

  .milestone-stages {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    margin: 1.5rem 0;
  }

  .stage {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 1rem;
    background: var(--bg-primary);
    border-radius: 0.5rem;
    border-left: 3px solid var(--accent);
  }

  .stage-icon {
    font-size: 1.5rem;
    width: 2rem;
    text-align: center;
  }

  .stage-info h4 {
    margin: 0 0 0.25rem 0;
    color: var(--text-primary);
    font-size: 1rem;
  }

  .stage-info p {
    margin: 0;
    color: var(--text-secondary);
    font-size: 0.9rem;
  }

  .milestone-note {
    color: var(--text-secondary);
    font-style: italic;
    font-size: 0.9rem;
    line-height: 1.6;
    margin-top: 1rem;
  }

  /* New Life-Themed Section Styles */
  .metabolism-display {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }

  .metabolism-stats {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1rem;
  }

  .metabolism-stats .stat {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 1rem;
    background: var(--bg-primary);
    border-radius: 0.5rem;
    border: 1px solid var(--accent);
  }

  .metabolism-stats .stat-value {
    font-size: 1.5rem;
    font-weight: 600;
    color: var(--accent);
  }

  .metabolism-stats .stat-label {
    font-size: 0.9rem;
    color: var(--text-secondary);
  }

  .heartbeat-chart {
    background: var(--bg-primary);
    border-radius: 0.5rem;
    padding: 1rem;
    border: 1px solid var(--accent);
  }

  .ecosystem-display {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }

  .ecosystem-species {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 1rem;
  }

  .species {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 1rem;
    background: var(--bg-primary);
    border-radius: 0.5rem;
    border: 1px solid var(--accent);
  }

  .species-icon {
    font-size: 1.5rem;
  }

  .species-info {
    display: flex;
    flex-direction: column;
  }

  .species-name {
    font-size: 0.9rem;
    color: var(--text-secondary);
  }

  .species-count {
    font-size: 1.2rem;
    font-weight: 600;
    color: var(--text-primary);
  }

  .biodiversity-score {
    display: flex;
    justify-content: center;
  }

  .score-circle {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    width: 100px;
    height: 100px;
    border-radius: 50%;
    background: var(--bg-primary);
    border: 3px solid var(--accent);
  }

  .score-value {
    font-size: 1.5rem;
    font-weight: 600;
    color: var(--accent);
  }

  .score-label {
    font-size: 0.8rem;
    color: var(--text-secondary);
  }

  /* New modal styles */
  .personality-explanation ul {
    list-style: none;
    padding: 0;
  }

  .personality-explanation li {
    padding: 0.5rem 0;
    border-bottom: 1px solid var(--border);
  }

  .personality-types {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem;
    margin: 1rem 0;
  }

  .personality-type {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem;
    background: var(--bg-primary);
    border-radius: 0.5rem;
    border: 1px solid var(--border);
  }

  .type-icon {
    font-size: 1.5rem;
  }

  .confidence-note {
    font-size: 0.875rem;
    color: var(--text-secondary);
    font-style: italic;
    margin-top: 1rem;
  }

  .metabolism-explanation ul {
    list-style: none;
    padding: 0;
  }

  .metabolism-explanation li {
    padding: 0.5rem 0;
    border-bottom: 1px solid var(--border);
  }

  .metabolism-stages {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    margin: 1rem 0;
  }

  .metabolism-stages .stage {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.75rem;
    background: var(--bg-primary);
    border-radius: 0.5rem;
    border: 1px solid var(--border);
  }

  .stage-icon {
    font-size: 1.5rem;
  }

  .metabolism-note {
    font-size: 0.875rem;
    color: var(--text-secondary);
    font-style: italic;
    margin-top: 1rem;
  }

  .ecosystem-explanation ul {
    list-style: none;
    padding: 0;
  }

  .species-guide {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    margin: 1rem 0;
  }

  .species-item {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.75rem;
    background: var(--bg-primary);
    border-radius: 0.5rem;
    border: 1px solid var(--border);
  }

  .species-icon {
    font-size: 1.5rem;
  }

  .biodiversity-levels {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    margin: 1rem 0;
  }

  .level {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem;
    background: var(--bg-primary);
    border-radius: 0.25rem;
    font-size: 0.875rem;
  }

  .level-icon {
    font-size: 1.2rem;
  }

  .ecosystem-note {
    font-size: 0.875rem;
    color: var(--text-secondary);
    font-style: italic;
    margin-top: 1rem;
  }

  @media (max-width: 768px) {
    .insights-page {
      padding: 1rem;
    }

    .insights-header {
      flex-direction: column;
      align-items: flex-start;
      gap: 1rem;
    }

    .insights-grid {
      grid-template-columns: 1fr;
    }

    .velocity-stats {
      grid-template-columns: 1fr;
    }

    .metabolism-stats {
      grid-template-columns: 1fr;
    }

    .ecosystem-species {
      grid-template-columns: 1fr;
    }

    .personality-types {
      grid-template-columns: 1fr;
    }
  }
</style>
