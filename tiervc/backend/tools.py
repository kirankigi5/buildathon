
# Industry revenue multiples
INDUSTRY_MULTIPLES = {
	"Software": 8.0,
	"SaaS": 8.5,
	"Business/Productivity Software": 8.0,
	"Healthcare": 6.0,
	"HealthTech": 6.5,
	"FinTech": 7.5,
	"Consumer": 4.0,
	"Electronics": 3.5,
	"Hardware": 3.5,
	"CleanTech": 5.0,
	"Default": 5.5,
}

# Stage growth rates
STAGE_GROWTH_RATES = {
	"Pre-seed": 2.5,
	"Seed": 2.2,
	"Series A": 1.8,
	"Series B": 1.5,
	"Default": 2.0,
}

def financial_projection_tool(total_raised, industry, stage):
	multiple = INDUSTRY_MULTIPLES.get(industry, INDUSTRY_MULTIPLES["Default"])
	growth_rate = STAGE_GROWTH_RATES.get(stage, STAGE_GROWTH_RATES["Default"])
	year1 = max(total_raised * 1.2, 0.5 if total_raised < 1 else 0)
	year2 = year1 * growth_rate
	year3 = year2 * growth_rate * 0.85
	valuation_low = year3 * multiple * 0.7
	valuation_high = year3 * multiple * 1.3
	valuation_mid = (valuation_low + valuation_high) / 2
	summary = (
		f"Industry: {industry}, Stage: {stage}, Year 1 Revenue: ${year1:.2f}M, "
		f"Year 3 Revenue: ${year3:.2f}M, Valuation Range: ${valuation_low:.2f}M - ${valuation_high:.2f}M"
	)
	return {
		"year1_revenue_est": year1,
		"year3_revenue_est": year3,
		"valuation_low_m": valuation_low,
		"valuation_mid_m": valuation_mid,
		"valuation_high_m": valuation_high,
		"industry_multiple": multiple,
		"summary": summary,
	}

def assign_tier(score: int) -> tuple[int, str, str]:
	if score >= 75:
		return (1, "🟢 Tier 1 - Immediate Accept", "Yes")
	elif score >= 50:
		return (2, "🟡 Tier 2 - Interview Further", "Maybe")
	else:
		return (3, "🔴 Tier 3 - Reject", "No")

def calculate_confidence(score: int) -> str:
	dist_75 = abs(score - 75)
	dist_50 = abs(score - 50)
	min_dist = min(dist_75, dist_50)
	if min_dist > 15:
		return "High"
	elif min_dist > 7:
		return "Medium"
	else:
		return "Low"
