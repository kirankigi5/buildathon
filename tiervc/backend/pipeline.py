
import time
import asyncio
from typing import List, Callable
from schemas import StartupInput, StartupResult
from agents import nemotron_agent, claude_agent, gpt4_judge
from tools import financial_projection_tool, assign_tier, calculate_confidence

async def evaluate_startup(startup: StartupInput, emit: Callable) -> StartupResult:
	start_time = time.time()
	emit("log", startup.name, "🧠 Nemotron orchestrator activated", "nemotron")
	emit("log", startup.name, "🔧 Calling financial_projection_tool()", "system")
	valuation = financial_projection_tool(startup.total_raised_m, startup.industry, startup.stage)
	emit("log", startup.name, f"✅ Tool: {valuation['summary']}", "system")
	emit("log", startup.name, "📈 Nemotron analyzing market opportunity...", "nemotron")
	nemotron_output = await nemotron_agent(startup.dict(), valuation)
	if isinstance(nemotron_output, str):
		nemotron_output = eval(nemotron_output)
	emit("log", startup.name, f"✅ Market score: {nemotron_output['market_score']}/100", "nemotron")
	emit("log", startup.name, "🤖 Claude evaluating founding team...", "claude")
	claude_output = await claude_agent(startup.dict())
	emit("log", startup.name, f"✅ Team score: {claude_output['team_score']}/100", "claude")
	emit("log", startup.name, "⚖️ Debate: Pro vs Contra", "system")
	pro_argument = nemotron_output.get("pro_argument", "")
	contra_argument = claude_output.get("contra_argument", "")
	emit("log", startup.name, f"🟢 Pro: {pro_argument}", "nemotron")
	emit("log", startup.name, f"🔴 Contra: {contra_argument}", "claude")
	emit("log", startup.name, "👨‍⚖️ GPT-4 judging debate...", "gpt4")
	judge_output = await gpt4_judge(startup.dict(), nemotron_output, claude_output)
	if isinstance(judge_output, str):
		judge_output = eval(judge_output)
	score = judge_output.get("final_score", 0)
	tier, tier_label, invest = assign_tier(score)
	confidence = calculate_confidence(score)
	emit("log", startup.name, f"🏆 Score: {score}/100 → {tier_label}", "system")
	result_dict = {
		"nemotron_output": nemotron_output,
		"claude_output": claude_output,
		"judge_output": judge_output
	}
	emit("result", startup.name, None, None, result_dict)
	processing_time = time.time() - start_time
	return StartupResult(
		name=startup.name,
		founder_name=startup.founder_name,
		linkedin_url=startup.linkedin_url,
		website=startup.website,
		tier=tier,
		tier_label=tier_label,
		score=score,
		invest=invest,
		confidence=confidence,
		top_pro=judge_output.get("top_pro", ""),
		top_risk=judge_output.get("top_risk", ""),
		processing_time=processing_time
	)

async def evaluate_batch(startups: List[StartupInput], emit: Callable) -> List[StartupResult]:
	emit("log", None, "🚀 Starting batch evaluation", "system")
	tasks = [evaluate_startup(s, emit) for s in startups]
	results = await asyncio.gather(*tasks)
	return results
