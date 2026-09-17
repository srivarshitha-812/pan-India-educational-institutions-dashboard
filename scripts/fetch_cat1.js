const crypto = require('crypto');
const https = require('https');
const fs = require('fs');
const path = require('path');

function getEncryptedValue(val) {
    if (val === null || val === undefined || val === '') return '';
    const passphrase = '0123456789123456';
    const salt = crypto.randomBytes(16);
    const iv = crypto.randomBytes(16);
    const key = crypto.pbkdf2Sync(passphrase, salt, 1000, 16, 'sha1');
    const cipher = crypto.createCipheriv('aes-128-cbc', key, iv);
    let encrypted = cipher.update(val.toString(), 'utf8', 'base64');
    encrypted += cipher.final('base64');
    return Buffer.from(`${iv.toString('hex')}::${salt.toString('hex')}::${encrypted}`).toString('base64');
}

console.log('Testing Category 1 fetch with stateCode=ALL...');
const reqPath = `/aisheinstitutemanagement/institutionDirectory%20/getCollegeList?districtcode=&stateCode=${encodeURIComponent(getEncryptedValue('ALL'))}&typeid=${encodeURIComponent(getEncryptedValue('1'))}&surveyYear=${encodeURIComponent(getEncryptedValue(2020))}&universityId=&universityType=`;

const options = {
    hostname: 'pdf.aishe.nic.in',
    port: 443,
    path: reqPath,
    method: 'GET',
    headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://dashboard.aishe.gov.in/',
        'Origin': 'https://dashboard.aishe.gov.in',
        'Accept': 'application/json, text/plain, */*'
    },
    rejectUnauthorized: false
};

const startTime = Date.now();
const req = https.request(options, (res) => {
    console.log('Response Status:', res.statusCode);
    console.log('Content-Length:', res.headers['content-length']);
    
    const chunks = [];
    let totalBytes = 0;
    
    res.on('data', (c) => {
        chunks.push(c);
        totalBytes += c.length;
        if (totalBytes % (5 * 1024 * 1024) < c.length) {
            console.log(`Received ${(totalBytes / (1024 * 1024)).toFixed(1)} MB...`);
        }
    });

    res.on('end', () => {
        const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
        console.log(`Finished download in ${elapsed}s! Total size: ${(totalBytes / (1024*1024)).toFixed(2)} MB`);
        const fullBuf = Buffer.concat(chunks);
        try {
            const parsed = JSON.parse(fullBuf.toString('utf8'));
            const count = parsed.institutionDirectoryDto ? parsed.institutionDirectoryDto.length : 0;
            console.log(`Successfully parsed! Total records: ${count}`);
            
            // Save to disk checkpoint
            fs.mkdirSync('data/raw/aishe', { recursive: true });
            fs.writeFileSync('data/raw/aishe/aishe_category_1_affiliated.json', fullBuf);
            console.log('Saved to data/raw/aishe/aishe_category_1_affiliated.json');
        } catch(e) {
            console.error('Parse error:', e);
        }
    });
});

req.on('error', (e) => {
    console.error('Request error:', e);
});

req.end();
