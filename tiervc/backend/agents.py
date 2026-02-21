
import os
import json
import re
from dotenv import load_dotenv
load_dotenv()

from openai import AsyncOpenAI
from anthropic import AsyncAnthropic

# Nemotron via OpenRouter
nemotron_client = AsyncOpenAI(base_url="https://openrouter.ai/api/v1", api_key=os.getenv("OPENROUTER_API_KEY"))
# Claude via Anthropic
claude_client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
# GPT-4 via OpenAI
gpt4_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def nemotron_agent(startup: dict, valuation: dict) -> dict:
	prompt = f"""
You are a VC market analyst. Given this startup and financial model, evaluate market opportunity and build strongest pro-investment argument.
Startup:
Name: {startup.get('name')}
Description: {startup.get('description')}
Industry: {startup.get('industry')}
Stage: {startup.get('stage')}
Total Raised: {startup.get('total_raised_m')}M
Valuation Summary: {valuation.get('summary')}
Return JSON: {{ "market_score": 0-100, "market_summary": "2 sentences", "pro_argument": "1 sentence strongest reason to invest", "upside_potential": "1 sentence key opportunity" }}
"""
	response = await nemotron_client.chat.completions.create(
		model="nvidia/llama-3.1-nemotron-70b-instruct",
		messages=[{"role": "user", "content": prompt}],
		response_format={"type": "json_object"},
		temperature=0.7,
		max_tokens=400
	)
	return response.choices[0].message.content if hasattr(response.choices[0].message, 'content') else json.loads(response.choices[0].message)

async def claude_agent(startup: dict) -> dict:
	prompt = f"""
You are a VC team analyst and devil's advocate. Evaluate founding team and build strongest contra-investment argument.
Startup:
Name: {startup.get('name')}
Description: {startup.get('description')}
Founder: {startup.get('founder_name')}
LinkedIn: {startup.get('linkedin_url')}
Stage: {startup.get('stage')}
Industry: {startup.get('industry')}
Return JSON: {{ "team_score": 0-100, "team_summary": "2 sentences", "contra_argument": "1 sentence strongest reason NOT to invest", "key_risk": "1 sentence biggest risk" }}
"""
	response = await claude_client.messages.create(
		model="claude-3-5-haiku-20241022",
		max_tokens=400,
		temperature=0.7,
		messages=[{"role": "user", "content": prompt}]
	)
	text = response.content[0].text if hasattr(response.content[0], 'text') else response.content[0]
	try:
		return json.loads(text)
	except Exception:
		# Fallback: extract JSON object with regex
		match = re.search(r'{.*}', text, re.DOTALL)
		if match:
			try:
				return json.loads(match.group(0))
			except Exception:
				return {}
		return {}

async def gpt4_judge(startup: dict, nemotron_output: dict, claude_output: dict) -> dict:
	prompt = f"""
You are the final investment committee judge. Weigh pro vs contra arguments and assign a final score.
Startup:
Name: {startup.get('name')}
Description: {startup.get('description')}
Industry: {startup.get('industry')}
Stage: {startup.get('stage')}
Total Raised: {startup.get('total_raised_m')}M
Nemotron Output: {json.dumps(nemotron_output)}
Claude Output: {json.dumps(claude_output)}
Scoring: 75-100 = strong invest, 50-74 = interview/diligence, 0-49 = pass.
Return JSON: {{ "final_score": 0-100, "reasoning": "2 sentences", "top_pro": "1 sentence best pro argument", "top_risk": "1 sentence biggest risk" }}
"""
	response = await gpt4_client.chat.completions.create(
		model="gpt-4o-mini",
		messages=[{"role": "user", "content": prompt}],
		response_format={"type": "json_object"},
		temperature=0.5,
		max_tokens=400
	)
	return response.choices[0].message.content if hasattr(response.choices[0].message, 'content') else json.loads(response.choices[0].message)
