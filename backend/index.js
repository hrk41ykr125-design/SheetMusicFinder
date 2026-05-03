import { load } from 'cheerio';

const searchCache = new Map();

export default {
  async fetch(request, env) {
    // Handle CORS preflight
    if (request.method === 'OPTIONS') {
      return new Response(null, {
        headers: {
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Methods': 'POST, OPTIONS',
          'Access-Control-Allow-Headers': 'Content-Type',
        },
      });
    }

    if (request.method !== 'POST') {
      return new Response('Method Not Allowed', { status: 405 });
    }

    const url = new URL(request.url);
    if (url.pathname === '/api/search') {
      try {
        const body = await request.json();
        const { song_name, artist, instrument, sites } = body;

        if (!song_name) {
          return new Response(JSON.stringify({ error: 'Song name is required' }), { status: 400 });
        }

        const selectedSites = sites || ["piascore", "atelise", "web_free"];
        const cacheKey = `${song_name.toLowerCase()}:${(artist || '').toLowerCase()}:${selectedSites.sort().join(',')}`;

        let allResults;
        if (searchCache.has(cacheKey)) {
          console.log(`Cache hit: ${cacheKey}`);
          allResults = searchCache.get(cacheKey);
        } else {
          console.log(`Cache miss: ${cacheKey}`);
          allResults = await searchAll(song_name, artist, selectedSites);
          searchCache.set(cacheKey, allResults);
          
          // Limit cache size
          if (searchCache.size > 100) {
            const firstKey = searchCache.keys().next().value;
            searchCache.delete(firstKey);
          }
        }

        // Filter by instrument
        const filtered = allResults.filter(r => {
          if (!instrument) return true;
          return r.details.toLowerCase().includes(instrument.toLowerCase());
        }).map(r => ({
          ...r,
          instrument: instrument || "指定なし"
        }));

        return new Response(JSON.stringify(filtered), {
          headers: {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
          },
        });
      } catch (err) {
        return new Response(JSON.stringify({ error: err.message }), { status: 500 });
      }
    }

    return new Response('Not Found', { status: 404 });
  }
};

async function fetchHTML(url) {
  try {
    const response = await fetch(url, {
      headers: { 'User-Agent': 'Mozilla/5.0' }
    });
    if (!response.ok) return null;
    return await response.text();
  } catch (e) {
    console.error(`Fetch error ${url}:`, e);
    return null;
  }
}

function cleanText(text) {
  const cleaned = text.replace(/\s+/g, ' ').trim();
  return cleaned.length > 80 ? cleaned.substring(0, 77) + '...' : cleaned;
}

async function scrapePiascore(songName, artist) {
  const searchTerm = `${songName} ${artist || ''}`.trim();
  const query = encodeURIComponent(searchTerm);
  const baseUrl = `https://store.piascore.com/search?n=${query}`;
  
  const results = [];
  const html = await fetchHTML(baseUrl);
  if (!html) return results;

  const $ = load(html);
  $('a[href*="/scores/"]').each((i, el) => {
    const href = $(el).attr('href');
    const text = $(el).text().trim();
    if (href && text.length > 5 && text.toLowerCase().includes(songName.toLowerCase())) {
      results.push({
        site_name: 'Piascore',
        details: cleanText(text),
        url: href.startsWith('/') ? `https://store.piascore.com${href}` : href
      });
    }
  });

  // Unique results
  return Array.from(new Map(results.map(r => [r.url, r])).values());
}

async function scrapeAtelise(songName, artist) {
  const searchTerm = `${songName} ${artist || ''}`.trim();
  const query = encodeURIComponent(searchTerm);
  const url = `https://www.at-elise.com/goods/list?free_word=${query}`;
  
  const results = [];
  const html = await fetchHTML(url);
  if (!html) return results;

  const $ = load(html);
  $('a[href*="/elise/"]').each((i, el) => {
    const href = $(el).attr('href');
    const text = $(el).text().trim();
    if (href && text.length > 5 && text.toLowerCase().includes(songName.toLowerCase())) {
      results.push({
        site_name: '＠ELISE',
        details: cleanText(text),
        url: href.startsWith('/') ? `https://www.at-elise.com${href}` : href
      });
    }
  });

  return Array.from(new Map(results.map(r => [r.url, r])).values());
}

async function scrapeWebFree(songName, artist) {
  const searchTerm = `無料 楽譜 ${songName} ${artist || ''}`.trim();
  const query = encodeURIComponent(searchTerm);
  const url = `https://html.duckduckgo.com/html/?q=${query}`;
  
  const results = [];
  const html = await fetchHTML(url);
  if (!html) return results;

  const $ = load(html);
  $('.result').each((i, el) => {
    const a = $(el).find('.result__a');
    const title = a.text().trim();
    let href = a.attr('href');
    const snippet = $(el).find('.result__snippet').text().trim();

    if (href && href.includes('uddg=')) {
      href = decodeURIComponent(href.split('uddg=')[1].split('&')[0]);
    }

    if (title.toLowerCase().includes(songName.toLowerCase()) || snippet.toLowerCase().includes(songName.toLowerCase())) {
      results.push({
        site_name: 'Web無料検索',
        details: cleanText(title),
        url: href
      });
    }
    if (results.length >= 15) return false;
  });

  return results;
}

async function searchAll(songName, artist, sites) {
  const tasks = [];
  if (sites.includes('piascore')) tasks.push(scrapePiascore(songName, artist));
  if (sites.includes('atelise')) tasks.push(scrapeAtelise(songName, artist));
  if (sites.includes('web_free')) tasks.push(scrapeWebFree(songName, artist));

  const resultsLists = await Promise.all(tasks);
  return resultsLists.flat();
}
