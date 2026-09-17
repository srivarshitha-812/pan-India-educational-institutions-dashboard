const https = require('https');

const options = {
    hostname: 'pdf.aishe.nic.in',
    port: 443,
    path: '/aisheinstitutemanagement/dashboard/enrollment?stateCode=ALL',
    method: 'GET',
    headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://dashboard.aishe.gov.in/',
        'Origin': 'https://dashboard.aishe.gov.in',
        'Accept': 'application/json, text/plain, */*'
    },
    rejectUnauthorized: false
};

const req = https.request(options, (res) => {
    let data = '';
    res.on('data', c => data += c);
    res.on('end', () => {
        try {
            const parsed = JSON.parse(data);
            console.log('Status:', res.statusCode);
            console.log('Data sample:', Array.isArray(parsed) ? parsed.slice(0, 5) : parsed);
        } catch(e) {
            console.log('Error:', e, data.slice(0, 200));
        }
    });
});
req.on('error', console.error);
req.end();
