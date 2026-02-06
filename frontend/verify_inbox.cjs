const puppeteer = require('puppeteer');

(async () => {
    const browser = await puppeteer.launch({
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });
    const page = await browser.newPage();

    try {
        console.log('1. Navigating to Login...');
        await page.goto('http://localhost:56000/login', { waitUntil: 'networkidle0' });

        console.log('2. Logging in...');
        await page.type('input[name="username"]', 'admin');
        await page.type('input[name="password"]', 'admin123');
        await page.click('button[type="submit"]');

        // Wait for navigation to dashboard
        await page.waitForNavigation({ waitUntil: 'networkidle0' });
        console.log('   Logged in successfully.');

        console.log('3. Navigating to Review Inbox...');
        await page.goto('http://localhost:56000/review-inbox', { waitUntil: 'networkidle0' });

        // Wait for list to load initially
        try {
            await page.waitForSelector('img[alt="Document"]', { timeout: 10000 });
            console.log('   Review Inbox loaded.');
        } catch (e) {
            console.log('   No documents found initially.');
        }

        // Screenshot initial state
        await page.screenshot({ path: 'review_inbox_batch_start.png' });
        console.log('   Screenshot saved: review_inbox_batch_start.png');

        // Loop through entries
        let entryCount = 0;
        while (true) {
            // Wait for either an image (entry) or check if list is empty
            try {
                await page.waitForSelector('img[alt="Document"]', { timeout: 5000 });
            } catch (e) {
                console.log("   No more documents found (or timeout waiting for next).");
                break;
            }

            const approveBtn = await page.$('button.MuiButton-containedSuccess');
            if (!approveBtn) {
                console.log("   Approve button not found (maybe processing?), stopping.");
                break;
            }

            console.log(`4.${entryCount + 1} Clicking Approve using UI...`);

            // Click and verify
            await approveBtn.click();

            // Wait for toast
            try {
                await page.waitForSelector('.MuiAlert-message', { timeout: 5000 });
                const toastText = await page.$eval('.MuiAlert-message', el => el.textContent);
                console.log(`   Toast: "${toastText}"`);

                if (!toastText.includes('Successfully')) {
                    console.warn('   ⚠️ Unexpected toast message.');
                }
            } catch (e) {
                console.warn("   Toast missed or didn't appear.");
            }

            // Wait for the list to refresh (old image gone or new one loaded)
            await new Promise(r => setTimeout(r, 2000));
            entryCount++;

            if (entryCount >= 5) break;
        }

        if (entryCount > 0) {
            console.log(`✅ SUCCESS: Approved ${entryCount} documents.`);
        } else {
            console.error('❌ FAILURE: No documents were processed.');
            process.exit(1);
        }

    } catch (error) {
        console.error('❌ ERROR:', error);
        process.exit(1);
    } finally {
        await browser.close();
    }
})();
