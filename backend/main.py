from fastapi import FastAPI, HTTPException
from backend.contracts import DealContext, Recommendation
from backend.ingestion.deals import list_deals
from backend.graph.context import build_deal_context
from backend.decision.hybrid import analyze_deal_envelope
from backend.api.phase3 import deal_initial_analysis, pipeline_initial_analysis, pipeline_priorities

app = FastAPI(title='DealCompass', version='0.1.0')

@app.get('/health')
def health():
    return {'status': 'ok', 'schema_version': 'v1', 'snapshot_date': '2026-10-01'}

@app.get('/api/deals')
def deals():
    return {'schema_version': 'v1', 'snapshot_date': '2026-10-01', 'items': list_deals()}

def require_deal(deal_id: str):
    if deal_id not in {d.deal_id for d in list_deals()}:
        raise HTTPException(404, detail={'code': 'DEAL_NOT_FOUND', 'message': 'Deal tidak ditemukan.'})

@app.get('/api/deals/{deal_id}', response_model=DealContext)
def detail(deal_id: str):
    require_deal(deal_id)
    try:
        return build_deal_context(deal_id)
    except NotImplementedError as e:
        raise HTTPException(501, detail={'code': 'NOT_IMPLEMENTED', 'message': str(e)}) from e

@app.post('/api/deals/{deal_id}/analyze', response_model=Recommendation)
def analyze(deal_id: str):
    """Recommendation v1 saja; memakai workflow, cache dan dedup yang sama dengan /analysis."""
    require_deal(deal_id)
    try:
        return analyze_deal_envelope(deal_id, context=build_deal_context(deal_id))['recommendation']
    except NotImplementedError as e:
        raise HTTPException(501, detail={'code': 'NOT_IMPLEMENTED', 'message': str(e)}) from e


@app.post('/api/deals/{deal_id}/analysis')
def analysis(deal_id: str, refresh: bool = False):
    """Analisis aktif halaman deal: Recommendation + metadata asal/cache. refresh=true hanya dari tombol Refresh."""
    require_deal(deal_id)
    try:
        return analyze_deal_envelope(deal_id, refresh=refresh, context=build_deal_context(deal_id))
    except NotImplementedError as e:
        raise HTTPException(501, detail={'code': 'NOT_IMPLEMENTED', 'message': str(e)}) from e


@app.get('/api/deals/{deal_id}/initial-analysis')
def initial_analysis(deal_id: str):
    require_deal(deal_id)
    return deal_initial_analysis(deal_id)

@app.get('/api/pipeline/initial-analysis')
def pipeline_diagnostics():
    return pipeline_initial_analysis()

@app.get('/api/pipeline/priorities')
def priorities():
    return pipeline_priorities()
