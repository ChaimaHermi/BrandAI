export function normalizeArray(value) {
  return Array.isArray(value) ? value : [];
}

export function mapMarketingPlan(payload) {
  if (!payload) return null;

  const plan = payload.result_json || payload;

  return {
    positioning: plan.positioning || {},
    targeting: plan.targeting || {},
    messaging: plan.messaging || {},
    channels: {
      primaryChannels: normalizeArray(plan.channels?.primary_channels),
      secondaryChannels: normalizeArray(plan.channels?.secondary_channels),
      justification: plan.channels?.justification || "",
    },
    contentDirection: {
      angles: normalizeArray(plan.content_direction?.angles),
      contentGoals: normalizeArray(plan.content_direction?.content_goals),
      platformFocus: normalizeArray(plan.content_direction?.platform_focus),
      tone: plan.content_direction?.tone || "",
    },
    pricingStrategy: plan.pricing_strategy || {},
    goToMarket: {
      targetFirstUsers: plan.go_to_market?.target_first_users || "",
      launchStrategy: plan.go_to_market?.launch_strategy || "",
      partnerships: normalizeArray(plan.go_to_market?.partnerships),
      earlyGrowthTactics: normalizeArray(plan.go_to_market?.early_growth_tactics),
    },
    actionPlan: {
      shortTerm: normalizeArray(plan.action_plan?.short_term),
      midTerm: normalizeArray(plan.action_plan?.mid_term),
      longTerm: normalizeArray(plan.action_plan?.long_term),
    },
    assumptions: normalizeArray(plan.assumptions),
    confidenceLevel: plan.confidence_level || "-",
  };
}
