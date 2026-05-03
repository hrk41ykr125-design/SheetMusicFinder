import httpx
import asyncio
from bs4 import BeautifulSoup
import urllib.parse

try:
    from js import fetch as js_fetch
    import asyncio
    IS_WORKER = True
except ImportError:
    IS_WORKER = False

async def fetch_html(url: str):
    if IS_WORKER:
        try:
            # Cloudflare Workers Python environment fetch
            response = await js_fetch(url, headers={"User-Agent": "Mozilla/5.0"})
            return await response.text()
        except Exception as e:
            print(f"Worker Fetch Error {url}: {e}")
            return None
    else:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            try:
                response = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
                response.raise_for_status()
                return response.text
            except Exception as e:
                print(f"Error fetching {url}: {e}")
                return None

def clean_text(text: str) -> str:
    # Remove excessive newlines and spaces
    cleaned = ' '.join(text.split())
    if len(cleaned) > 80:
        return cleaned[:77] + "..."
    return cleaned

async def scrape_piascore_page(url: str, song_name: str, artist: str = None):
    html = await fetch_html(url)
    results = []
    if not html:
        return results, html
        
    soup = BeautifulSoup(html, 'html.parser')
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        if '/scores/' in href and not href.endswith('/scores/'):
            text = a_tag.get_text(separator=" ", strip=True)
            if not text or len(text) < 5:
                continue
                
            match_song = song_name.lower() in text.lower()
            match_artist = not artist or artist.lower() in text.lower()
            
            if match_song and match_artist:
                results.append({
                    "site_name": "Piascore",
                    "details": clean_text(text),
                    "url": f"https://store.piascore.com{href}" if href.startswith('/') else href
                })
    return results, html

async def scrape_piascore(song_name: str, artist: str = None):
    search_term = f"{song_name} {artist}".strip() if artist else song_name
    query = urllib.parse.quote(search_term)
    base_url = f"https://store.piascore.com/search?n={query}"
    
    first_page_results, html = await scrape_piascore_page(base_url, song_name, artist)
    if not html:
        return first_page_results
        
    max_page = 1
    soup = BeautifulSoup(html, 'html.parser')
    for a in soup.find_all('a', href=True):
        if 'page=' in a['href']:
            try:
                page_num = int(a['href'].split('page=')[-1].split('&')[0])
                if page_num > max_page:
                    max_page = page_num
            except:
                pass
                
    max_page = min(max_page, 5) # Fetch up to 5 pages
    
    all_results = first_page_results
    if max_page > 1:
        tasks = []
        for p in range(2, max_page + 1):
            tasks.append(scrape_piascore_page(f"{base_url}&page={p}", song_name, artist))
            
        pages_results = await asyncio.gather(*tasks)
        for p_res, _ in pages_results:
            all_results.extend(p_res)
                
    seen = set()
    unique_results = []
    for r in all_results:
        if r["url"] not in seen:
            seen.add(r["url"])
            unique_results.append(r)
            
    return unique_results

async def scrape_printgakufu(song_name: str, instrument: str, artist: str = None):
    search_term = f"{song_name} {artist} {instrument}".strip() if artist else f"{song_name} {instrument}".strip()
    query = urllib.parse.quote(search_term)
    url = f"https://www.print-gakufu.com/search/result/?keyword={query}"
    html = await fetch_html(url)
    results = []
    
    if not html:
        return results
        
    soup = BeautifulSoup(html, 'html.parser')
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        if '/score/detail/' in href:
            text = a_tag.get_text(separator=" ", strip=True)
            if not text or len(text) < 5:
                continue
                
            match_song = song_name.lower() in text.lower()
            match_inst = not instrument or instrument.lower() in text.lower()
            match_artist = not artist or artist.lower() in text.lower()
            
            if match_song and match_inst and match_artist:
                results.append({
                    "site_name": "ぷりんと楽譜",
                    "instrument": instrument if instrument else "指定なし",
                    "details": clean_text(text),
                    "url": f"https://www.print-gakufu.com{href}" if href.startswith('/') else href
                })
                
    seen = set()
    unique_results = []
    for r in results:
        if r["url"] not in seen:
            seen.add(r["url"])
            unique_results.append(r)
            
    return unique_results

async def scrape_atelise(song_name: str, artist: str = None):
    search_term = f"{song_name} {artist}".strip() if artist else song_name
    query = urllib.parse.quote(search_term)
    url = f"https://www.at-elise.com/goods/list?free_word={query}"
    html = await fetch_html(url)
    results = []
    
    if not html:
        return results
        
    soup = BeautifulSoup(html, 'html.parser')
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        if '/elise/' in href:
            text = a_tag.get_text(separator=" ", strip=True)
            if not text or len(text) < 5:
                continue
                
            match_song = song_name.lower() in text.lower()
            match_artist = not artist or artist.lower() in text.lower()
            
            if match_song and match_artist:
                results.append({
                    "site_name": "＠ELISE",
                    "details": clean_text(text),
                    "url": f"https://www.at-elise.com{href}" if href.startswith('/') else href
                })
                
    seen = set()
    unique_results = []
    for r in results:
        if r["url"] not in seen:
            seen.add(r["url"])
            unique_results.append(r)
            
    return unique_results

async def scrape_web_free(song_name: str, artist: str = None):
    search_term = f"無料 楽譜 {song_name} {artist}".strip()
    query = urllib.parse.quote(search_term)
    url = f"https://html.duckduckgo.com/html/?q={query}"
    html = await fetch_html(url)
    results = []
    
    if not html:
        return results
        
    soup = BeautifulSoup(html, 'html.parser')
    for result in soup.find_all('div', class_='result'):
        a_title = result.find('a', class_='result__a')
        if not a_title:
            continue
            
        title = a_title.get_text(strip=True)
        href = a_title['href']
        if 'uddg=' in href:
            href = urllib.parse.unquote(href.split('uddg=')[1].split('&')[0])
            
        snippet = result.find('a', class_='result__snippet')
        snippet_text = snippet.get_text(strip=True) if snippet else ""
        
        if song_name.lower() in title.lower() or song_name.lower() in snippet_text.lower():
            results.append({
                "site_name": "Web無料検索",
                "details": clean_text(title),
                "url": href
            })
            
        if len(results) >= 15: # Fetch a bit more for free search
            break
            
    return results

async def search_all(song_name: str, artist: str = None, sites: list = None):
    """
    Run selected scrapers concurrently and aggregate results (All instruments).
    """
    if sites is None:
        sites = ["piascore", "atelise", "web_free"]
        
    tasks = []
    
    if "piascore" in sites:
        tasks.append(asyncio.create_task(scrape_piascore(song_name, artist)))
    
    if "atelise" in sites:
        tasks.append(asyncio.create_task(scrape_atelise(song_name, artist)))
        
    if "web_free" in sites:
        tasks.append(asyncio.create_task(scrape_web_free(song_name, artist)))
        
    if not tasks:
        return []
        
    results_lists = await asyncio.gather(*tasks)
    
    combined = []
    for r_list in results_lists:
        combined.extend(r_list)
        
    return combined
