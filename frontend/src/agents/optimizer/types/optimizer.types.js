/**
 * @typedef {'facebook'|'instagram'|'linkedin'} Platform
 */

/**
 * @typedef {Object} KpiData
 * @property {number|null} followers
 * @property {number|null} engagement_rate
 * @property {number|null} reach
 * @property {number|null} post_count
 * @property {number|null} total_engagement
 * @property {number|null} comments
 * @property {number|null} clicks
 * @property {number|null} shares
 */

/**
 * @typedef {Object} EvolutionPoint
 * @property {string} date
 * @property {number} value
 */

/**
 * @typedef {Object} TopPost
 * @property {string} id
 * @property {string} preview
 * @property {Platform} platform
 * @property {string|null} media_type
 * @property {number|null} likes
 * @property {number|null} comments
 * @property {number|null} reach
 * @property {string|null} permalink_url
 * @property {string} published_at
 */

/**
 * @typedef {Object} PlatformStats
 * @property {KpiData} kpis
 * @property {EvolutionPoint[]} evolution
 * @property {TopPost[]} top_posts
 * @property {Record<string, number>} reactions_breakdown
 */

/**
 * @typedef {Object} Recommendation
 * @property {string} platform
 * @property {string} summary
 * @property {{id:number,title:string,description:string,actions:string[],priority:'high'|'medium'|'low'}[]} recommendations
 * @property {string|null} generated_at
 */
