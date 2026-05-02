/**
 * @typedef {'global'|'facebook'|'instagram'|'linkedin'} Platform
 */

/**
 * @typedef {Object} KpiData
 * @property {number|null} followers
 * @property {number|null} engagement_rate
 * @property {number|null} reach
 * @property {number|null} post_count
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
 * @property {number|null} likes
 * @property {number|null} comments
 * @property {number|null} reach
 * @property {string} published_at
 */

/**
 * @typedef {Object} PlatformStats
 * @property {KpiData} kpis
 * @property {EvolutionPoint[]} evolution
 * @property {TopPost[]} top_posts
 */

/**
 * @typedef {Object} Recommendation
 * @property {string} platform
 * @property {string} summary
 * @property {string[]} actions
 * @property {string|null} generated_at
 */
