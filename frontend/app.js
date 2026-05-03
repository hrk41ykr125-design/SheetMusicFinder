// API configuration
const API_BASE_URL = window.location.hostname === '127.0.0.1' || window.location.hostname === 'localhost' 
    ? 'http://127.0.0.1:8000' 
    : 'https://sheet-music-api.hrk41ykr125.workers.dev'; 

document.getElementById('search-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const songName = document.getElementById('song-name').value;
    const artistName = document.getElementById('artist-name').value;
    const instrument = document.getElementById('instrument').value;
    
    // Get selected sites
    const selectedSites = Array.from(document.querySelectorAll('input[name="site"]:checked')).map(cb => cb.value);
    
    const btnText = document.querySelector('.btn-text');
    const spinner = document.getElementById('loading-spinner');
    const resultsContainer = document.getElementById('results-container');
    
    // UI Loading state
    btnText.textContent = '検索中...';
    spinner.classList.remove('hidden');
    resultsContainer.innerHTML = '';
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/search`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                song_name: songName,
                artist: artistName,
                instrument: instrument,
                sites: selectedSites
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const results = await response.json();
        
        if (results.length === 0) {
            resultsContainer.innerHTML = `
                <div class="glass-panel no-results">
                    <h3>該当する楽譜が見つかりませんでした。</h3>
                    <p style="margin-top: 0.5rem;">アーティスト名を追加して再検索するか、検索対象を広げてみてください。</p>
                </div>
            `;
        } else {
            results.forEach((result, index) => {
                const card = document.createElement('div');
                card.className = 'result-card';
                card.style.animationDelay = `${index * 0.1}s`;
                
                const isFree = result.site_name === 'Web無料検索';
                
                card.innerHTML = `
                    <div class="result-info">
                        <span class="site-badge" style="${isFree ? 'background: rgba(16, 185, 129, 0.1); color: #10b981;' : ''}">${result.site_name}</span>
                        <div class="result-details">${result.details}</div>
                        <div class="result-instrument">編成: ${result.instrument || '指定なし'}</div>
                    </div>
                    <a href="${result.url}" target="_blank" rel="noopener noreferrer" class="btn-download">
                        ${isFree ? '楽譜を見る' : '詳細・購入'}
                    </a>
                `;
                resultsContainer.appendChild(card);
            });
        }
        
    } catch (error) {
        console.error('Error fetching data:', error);
        resultsContainer.innerHTML = `
            <div class="glass-panel no-results" style="border-color: rgba(239, 68, 68, 0.5);">
                <h3>エラーが発生しました</h3>
                <p style="margin-top: 0.5rem; color: #fca5a5;">バックエンドサーバーに接続できないか、通信中に問題が発生しました。サーバーが起動しているか確認してください。</p>
            </div>
        `;
    } finally {
        // Reset UI
        btnText.textContent = '検索する';
        spinner.classList.add('hidden');
    }
});
