
import os
import json
import asyncio
import time
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, UploadFile, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from starlette.responses import JSONResponse
from typing import List

from schemas import LogEvent, StartupInput, StartupResult
from excel_handler import parse_excel, create_output_excel
from pipeline import evaluate_batch

app = FastAPI()
app.add_middleware(
	CORSMiddleware,
	allow_origins=["*"],
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)

latest_results: List[StartupResult] = []

@app.get("/")
async def root():
	return {"status": "TierVC API Running", "version": "1.0"}

@app.post("/evaluate")
async def evaluate(file: UploadFile):
	content = await file.read()
	try:
		startups, col_mapping = parse_excel(content)
	except Exception as e:
		return JSONResponse(status_code=400, content={"error": f"Failed to parse file: {str(e)}"})
	if not startups:
		return JSONResponse(status_code=400, content={"error": "No valid startups found in file. Please check header row and column mapping."})

	event_queue = asyncio.Queue()

	def emit(event_type, startup=None, message=None, agent=None, data=None):
		evt = LogEvent(type=event_type, startup=startup, message=message, agent=agent, data=data)
		event_queue.put_nowait(evt.dict())

	async def sse_stream():
		# a. mapping event
		yield f"data: {json.dumps({'type': 'mapping', 'mapping': col_mapping, 'count': len(startups)})}\n\n"
		# b. startups event
		yield f"data: {json.dumps({'type': 'startups', 'names': [s.name for s in startups]})}\n\n"
		# c. evaluation events
		task = asyncio.create_task(evaluate_batch(startups, emit))
		tier_counts = {1: 0, 2: 0, 3: 0}
		results = []
		while True:
			try:
				evt = await asyncio.wait_for(event_queue.get(), timeout=60)
			except asyncio.TimeoutError:
				yield f"data: {json.dumps({'type': 'error', 'message': 'Timeout waiting for event.'})}\n\n"
				break
			if evt == "__DONE__":
				break
			if evt["type"] == "result":
				judge = evt["data"]["judge_output"]
				tier = judge.get("final_score", 0)
				t, _, _ = assign_tier(tier)
				tier_counts[t] += 1
				res = StartupResult(
					name=evt["startup"],
					founder_name=evt["data"]["claude_output"].get("founder_name", ""),
					linkedin_url=evt["data"]["claude_output"].get("linkedin_url", ""),
					website=evt["data"]["claude_output"].get("website", ""),
					tier=t,
					tier_label=assign_tier(tier)[1],
					score=judge.get("final_score", 0),
					invest=assign_tier(tier)[2],
					confidence=calculate_confidence(judge.get("final_score", 0)),
					top_pro=judge.get("top_pro", ""),
					top_risk=judge.get("top_risk", ""),
					processing_time=evt["data"]["judge_output"].get("processing_time", 0)
				)
				results.append(res)
			yield f"data: {json.dumps(evt)}\n\n"
		global latest_results
		latest_results = results
		# d. complete event
		yield f"data: {json.dumps({'type': 'complete', 'tier_counts': tier_counts, 'total': len(results)})}\n\n"

	headers = {
		"Cache-Control": "no-cache",
		"X-Accel-Buffering": "no"
	}
	return StreamingResponse(sse_stream(), media_type="text/event-stream", headers=headers)

@app.get("/download")
async def download():
	if not latest_results:
		return JSONResponse(status_code=404, content={"error": "No results available. Please run evaluation first."})
	excel_bytes = create_output_excel(latest_results)
	headers = {
		"Content-Disposition": "attachment; filename=TierVC_results.xlsx"
	}
	return Response(content=excel_bytes, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers=headers)

if __name__ == "__main__":
	import uvicorn
	uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
