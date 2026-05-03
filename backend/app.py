from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
try:
    from workers import WorkerEntrypoint
    import asgi
    IS_WORKER = True
except ImportError:
    IS_WORKER = False
import scrapers
import asyncio

app = FastAPI(title="楽譜検索ナビ API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SearchRequest(BaseModel):
    song_name: str
    artist: Optional[str] = None
    instrument: str
    sites: Optional[List[str]] = ["piascore", "atelise", "web_free"]

class SearchResult(BaseModel):
    site_name: str
    instrument: str
    details: str
    url: str

# Simple memory cache
search_cache = {}

@app.post("/api/search", response_model=List[SearchResult])
async def search_sheet_music(request: SearchRequest):
    if not request.song_name:
        raise HTTPException(status_code=400, detail="Song name is required")
    
    # Normalize sites for cache key
    sites_list = sorted(request.sites) if request.sites else []
    cache_key = f"{request.song_name.lower()}:{request.artist.lower() if request.artist else ''}:{','.join(sites_list)}"
    
    # Check cache
    if cache_key in search_cache:
        print(f"Cache hit for: {cache_key}")
        all_results = search_cache[cache_key]
    else:
        print(f"Cache miss for: {cache_key}")
        # Run scrapers for ALL instruments (instrument=None is now implied by scrapers.py)
        all_results = await scrapers.search_all(request.song_name, request.artist, request.sites)
        # Store in cache
        search_cache[cache_key] = all_results
        
        # Simple cache cleanup if it grows too large
        if len(search_cache) > 100:
            search_cache.pop(next(iter(search_cache)))

    # Filter results by instrument
    instrument = request.instrument
    formatted = []
    
    for r in all_results:
        # Filter logic: if instrument is specified, check if it's in the details/text
        # Scrapers already return clean_text in 'details'
        details = r.get("details", "")
        
        if not instrument or instrument.lower() in details.lower():
            formatted.append(SearchResult(
                site_name=r.get("site_name", "Unknown"),
                instrument=instrument if instrument else "指定なし",
                details=details,
                url=r.get("url", "")
            ))
            
    return formatted

if IS_WORKER:
    class Default(WorkerEntrypoint):
        async def fetch(self, request):
            return await asgi.fetch(app, request, self.env)
