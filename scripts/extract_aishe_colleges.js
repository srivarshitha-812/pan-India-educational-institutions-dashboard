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

const CATEGORIES = [
    { id: '1', name: 'Affiliated Colleges', file: 'aishe_category_1_affiliated.json' },
    { id: '2', name: 'Constituent / University Colleges', file: 'aishe_category_2_constituent.json' },
    { id: '3', name: 'PG Centre / Off-Campus Centres', file: 'aishe_category_3_pg_centres.json' },
    { id: '4', name: 'Recognized Centres', file: 'aishe_category_4_recognized_centres.json' },
    { id: '5', name: 'Autonomous Colleges', file: 'aishe_category_5_autonomous.json' }
];

const RAW_DIR = path.join(__dirname, '..', 'data', 'raw', 'aishe');
fs.mkdirSync(RAW_DIR, { recursive: true });

function fetchCategory(cat) {
    return new Promise((resolve, reject) => {
        const targetPath = path.join(RAW_DIR, cat.file);
        if (fs.existsSync(targetPath)) {
            const existing = JSON.parse(fs.readFileSync(targetPath, 'utf8'));
            const dtos = existing.institutionDirectoryDto || [];
            if (dtos.length > 0) {
                console.log(`[Cache Hit] Category ${cat.id} (${cat.name}): already saved with ${dtos.length} records.`);
                return resolve(dtos);
            }
        }

        console.log(`[Downloading] Category ${cat.id} (${cat.name})...`);
        const reqPath = `/aisheinstitutemanagement/institutionDirectory%20/getCollegeList?districtcode=&stateCode=${encodeURIComponent(getEncryptedValue('ALL'))}&typeid=${encodeURIComponent(getEncryptedValue(cat.id))}&surveyYear=${encodeURIComponent(getEncryptedValue(2020))}&universityId=&universityType=`;

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

        const t0 = Date.now();
        const req = https.request(options, (res) => {
            const chunks = [];
            let bytes = 0;
            res.on('data', c => {
                chunks.push(c);
                bytes += c.length;
            });
            res.on('end', () => {
                const fullBuf = Buffer.concat(chunks);
                const elapsed = ((Date.now() - t0) / 1000).toFixed(1);
                try {
                    const parsed = JSON.parse(fullBuf.toString('utf8'));
                    const dtos = parsed.institutionDirectoryDto || [];
                    console.log(`  [Success] Category ${cat.id} (${cat.name}): ${dtos.length} records, ${(bytes/(1024*1024)).toFixed(2)} MB in ${elapsed}s`);
                    fs.writeFileSync(targetPath, fullBuf);
                    resolve(dtos);
                } catch(e) {
                    console.error(`  [Error] Category ${cat.id} parsing failed:`, e);
                    reject(e);
                }
            });
        });

        req.on('error', (e) => {
            console.error(`  [Network Error] Category ${cat.id}:`, e);
            reject(e);
        });

        req.end();
    });
}

async function run() {
    console.log('====================================================');
    console.log('AISHE Higher Education Colleges National Extraction');
    console.log('====================================================');
    let totalRaw = 0;
    for (const cat of CATEGORIES) {
        try {
            const records = await fetchCategory(cat);
            totalRaw += records.length;
        } catch(e) {
            console.error(`Fatal error in category ${cat.id}:`, e);
        }
    }
    console.log('----------------------------------------------------');
    console.log(`Total raw harvested college records: ${totalRaw}`);
    console.log('All categories saved in data/raw/aishe/');
    console.log('====================================================');
}

run();
