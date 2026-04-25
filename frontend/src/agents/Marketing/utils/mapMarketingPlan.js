export function normalizeArray(value) {
  return Array.isArray(value) ? value : [];
}

export function mapMarketingPlan(payload) {
  if (!payload) return null;

  const plan = payload.result_json || payload;
  const positioning = plan?.positioning ?? {};
  const messaging = plan?.messaging ?? {};
  const channels = plan?.channels ?? {};
  const contentStrategy = plan?.content_strategy ?? {};
  const budgetAllocation = plan?.budget_allocation ?? {};
  const actionPlan = plan?.action_plan ?? {};
  const goToMarket = plan?.go_to_market ?? {};

  const primaryChannelsDetailed = Object.entries(channels)
    .map(([channelName, node]) => {
      if (!node || typeof node !== "object" || Array.isArray(node)) return null;
      const displayName = String(channelName || "").trim();
      return {
        name: displayName
          ? displayName.charAt(0).toUpperCase() + displayName.slice(1)
          : "",
        role: node.role,
        justification: node.justification,
      };
    })
    .filter(Boolean);

  const asActions = (bucket) => normalizeArray(bucket?.actions);

  return {
    /* ── Positioning & Messaging ─────────────────────────────────── */
    positioning: {
      target_segment: positioning.target_segment,
      value_proposition: positioning.value_proposition,
      differentiation: positioning.differentiation,
      primary_persona: positioning.primary_persona,
      tagline_suggestion: positioning.tagline_suggestion,
    },

    messaging: {
      main_message:       messaging.main_message,
      pain_point_focus:   messaging.pain_point_focus,
      emotional_hook:     messaging.emotional_hook,
      vocabulary_to_use:  normalizeArray(messaging.vocabulary_to_use),
      vocabulary_to_avoid: normalizeArray(messaging.vocabulary_to_avoid),
    },

    /* ── Targeting (derived from positioning) ────────────────────── */
    targeting: {
      primary_persona: positioning.primary_persona,
      market_segment_focus: positioning.target_segment,
    },

    /* ── Channels ────────────────────────────────────────────────── */
    channels: {
      primaryChannelsDetailed,
    },

    /* ── Budget ──────────────────────────────────────────────────── */
    budgetAllocation: {
      project_type_identified: budgetAllocation.project_type_identified,
      reasoning: budgetAllocation.reasoning,
      currency: budgetAllocation.currency,
      total: budgetAllocation.total,
      breakdown: normalizeArray(budgetAllocation.breakdown),
    },

    /* ── Content Strategy ────────────────────────────────────────── */
    contentDirection: {
      platforms: {
        facebook: contentStrategy?.facebook,
        instagram: contentStrategy?.instagram,
        linkedin: contentStrategy?.linkedin,
        global_editorial: contentStrategy?.global_editorial,
      },
    },

    /* ── Go-to-Market ────────────────────────────────────────────── */
    goToMarket: {
      targetFirstUsers:   goToMarket.target_first_users,
      launchStrategy:     goToMarket.launch_strategy,
      partnerships:       normalizeArray(goToMarket.partnerships),
      earlyGrowthTactics: normalizeArray(goToMarket.early_growth_tactics),
    },

    /* ── Action Plan ─────────────────────────────────────────────── */
    actionPlan: {
      shortTerm:         asActions(actionPlan?.short_term),
      midTerm:           asActions(actionPlan?.mid_term),
      longTerm:          asActions(actionPlan?.long_term),
      shortTermMilestone: actionPlan?.short_term?.milestone,
      midTermMilestone:   actionPlan?.mid_term?.milestone,
      longTermMilestone:  actionPlan?.long_term?.milestone,
      shortTermDuration:  actionPlan?.short_term?.duration,
      midTermDuration:    actionPlan?.mid_term?.duration,
      longTermDuration:   actionPlan?.long_term?.duration,
    },

    /* ── Misc ────────────────────────────────────────────────────── */
    confidenceLevel: plan.confidence_level,
  };
}
