const crypto = require('crypto');

function getEncryptedValue(val) {
    if (val === null || val === undefined || val === '') return val;
    const passphrase = '0123456789123456';
    const salt = crypto.randomBytes(16); // 16 bytes = 32 hex
    const iv = crypto.randomBytes(16);   // 16 bytes = 32 hex
    const key = crypto.pbkdf2Sync(passphrase, salt, 1000, 16, 'sha1'); // CryptoJS default PBKDF2 hasher is SHA1!

    const cipher = crypto.createCipheriv('aes-128-cbc', key, iv);
    let encrypted = cipher.update(val.toString(), 'utf8', 'base64');
    encrypted += cipher.final('base64');

    const result = `${iv.toString('hex')}::${salt.toString('hex')}::${encrypted}`;
    return Buffer.from(result).toString('base64');
}

console.log('Test encrypt "ALL":', getEncryptedValue('ALL'));
console.log('Test encrypt "1":', getEncryptedValue('1'));
console.log('Test encrypt "2020":', getEncryptedValue(2020));
