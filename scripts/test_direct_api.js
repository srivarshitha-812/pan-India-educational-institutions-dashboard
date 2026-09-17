const crypto = require('crypto');
const https = require('https');

function getEncryptedValue(val) {
    if (val === null || val === undefined || val === '') return '';
    const passphrase = '0123456789123456';
    const salt = crypto.randomBytes(16);
    const iv = crypto.randomBytes(16);
    const key = crypto.pbkdf2Sync(passphrase, salt, 1000, 16, 'sha1');

    const cipher = crypto.createCipheriv('aes-128-cbc', key, iv);
    let encrypted = cipher.update(val.toString(), 'utf8', 'base64');
    encrypted += cipher.final('base64');

    const result = `${iv.toString('hex')}::${salt.toString('hex')}::${encrypted}`;
    return Buffer.from(result).toString('base64');
}

// Test with Category 3 (PG Centre / Off-Campus Centre) which has 248 records (fast!)
const districtcode = '';
const stateCode = getEncryptedValue('ALL');
const typeid = getEncryptedValue('3'); // 3 = PG Centre
const surveyYear = getEncryptedValue(2020);
const universityId = '';
const universityType = '';

const path = `/aisheinstitutemanagement/institutionDirectory%20/getCollegeList?districtcode=${encodeURIComponent(districtcode)}&stateCode=${encodeURIComponent(stateCode)}&typeid=${encodeURIComponent(typeid)}&surveyYear=${encodeURIComponent(surveyYear)}&universityId=${encodeURIComponent(universityId)}&universityType=${encodeURIComponent(universityType)}`;

console.log('Requesting:', 'https://pdf.aishe.nic.in' + path);

const options = {
    hostname: 'pdf.aishe.nic.in',
    port: 443,
    path: path,
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
    console.log('Status Code:', res.statusCode);
    console.log('Headers:', res.headers);
    let data = '';
    res.on('data', (chunk) => {
        data += chunk;
    });
    res.on('end', () => {
        console.log('Body length:', data.length);
        try {
            const parsed = JSON.parse(data);
            console.log('Parsed statusCode:', parsed.statusCode);
            const dtos = parsed.institutionDirectoryDto || [];
            console.log('Records returned:', dtos.length);
            if (dtos.length > 0) {
                console.log('First record sample:', dtos[0]);
            }
        } catch (e) {
            console.log('Raw body preview (500 chars):', data.slice(0, 500));
        }
    });
});

req.on('error', (e) => {
    console.error('Error:', e);
});

req.end();
