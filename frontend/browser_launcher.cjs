
const puppeteer = require('puppeteer');

(async () => {
    try {
        const browser = await puppeteer.launch({
            headless: true,
            args: [
                '--remote-debugging-port=9222',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--remote-debugging-address=0.0.0.0'
            ]
        });
        console.log('Browser started on port 9222');
        // Keep alive
        await new Promise(() => { });
    } catch (e) {
        console.error(e);
        process.exit(1);
    }
})();
