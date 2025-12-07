document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('search-form');
    const loading = document.getElementById('loading');
    const resultDiv = document.getElementById('result');
    const errorDiv = document.getElementById('error');
    const answerDiv = document.getElementById('answer');
    const sourcesDiv = document.getElementById('sources');
    const submitBtn = document.getElementById('submit-btn');
    const userInput = document.getElementById('user_input');

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        errorDiv.style.display = 'none';
        resultDiv.style.display = 'none';
        answerDiv.textContent = '';
        sourcesDiv.innerHTML = '';
        loading.style.display = 'block';
        submitBtn.disabled = true;

        const text = userInput.value.trim();
        if (!text) {
            errorDiv.textContent = 'Please enter a query.';
            errorDiv.style.display = 'block';
            loading.style.display = 'none';
            submitBtn.disabled = false;
            return;
        }

        try {
            const formData = new FormData();
            formData.append('user_input', text);

            const resp = await fetch('https://difficulties-claimed-session-bargains.trycloudflare.com/query', {
                method: 'POST',
                headers: {
                    "X-API-KEY": "ali12345" 
                },
                body: formData
            })

            if (!resp.ok) {
                const err = await resp.text();
                throw new Error(err || 'Server error');
            }
            const data = await resp.json();
            if (data.error) throw new Error(data.error);

            answerDiv.textContent = data.answer || 'No answer returned.';
            const sources = data.sources || [];

            if (sources.length === 0) {
                sourcesDiv.innerHTML = '<p class="small">No matching cars found.</p>';
            } else {
                sourcesDiv.innerHTML = '';
                sources.forEach(s => {
                    const div = document.createElement('div');
                    div.className = 'source-row';
                    div.innerHTML = `<strong>${s.make || ''} ${s.model || ''} (${s.year || ''})</strong>
                               <div class="small">Price: ${s.latest_price || '-'} • Mileage: ${s["mileage(km)"] || '-'} • Body: ${s.body_type || '-'}</div>
                               <div class="small">${s.title || ''}</div>`;
                    sourcesDiv.appendChild(div);
                });
            }

            resultDiv.style.display = 'block';

        } catch (err) {
            console.error(err);
            errorDiv.textContent = 'Error: ' + (err.message || 'Server error');
            errorDiv.style.display = 'block';
        } finally {
            loading.style.display = 'none';
            submitBtn.disabled = false;
        }
    });
});