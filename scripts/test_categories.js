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
    return Buffer.from(`${iv.toString('hex')}::${salt.toString('hex')}::${encrypted}`).toString('base64');
}

function fetchCategory(typeidVal, desc) {
    return new Promise((resolve, reject) => {
        const path = `/aisheinstitutemanagement/institutionDirectory%20/getCollegeList?districtcode=&stateCode=${encodeURIComponent(getEncryptedValue('ALL'))}&typeid=${encodeURIComponent(getEncryptedValue(typeidVal))}&surveyYear=${encodeURIComponent(getEncryptedValue(2020))}&universityId=&universityType=`;
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
            let data = '';
            res.on('data', c => data += c);
            res.on('end', () => {
                try {
                    const parsed = JSON.parse(data);
                    const dtos = parsed.institutionDirectoryDto || [];
                    console.log(`[Category ${typeidVal}: ${desc}] Status: ${parsed.statusCode}, Records: ${dtos.length}, Body size: ${(data.length / (1024*1024)).toFixed(2)} MB`);
                    resolve(dtos);
                } catch(e) {
                    console.log(`[Category ${typeidVal}: ${desc}] Parse error. Data len: ${data.length}`);
                    resolve([]);
                }
            });
        });
        req.on('error', reject);
        req.end();
    });
}

async function run() {
    await fetchCategory('2', 'Constituent / University College');
    await fetchCategory('3', 'PG Centre / Off-Campus Centre');
    await fetchCategory('4', 'Recognized Centre');
    await fetchCategory('5', 'Autonomous College');
}

run();
