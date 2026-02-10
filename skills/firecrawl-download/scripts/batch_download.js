const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const rootUrl = process.argv[2];
const outputBaseDir = process.argv[3];
const limit = parseInt(process.argv[4] || '50', 10);

if (!rootUrl || !outputBaseDir) {
    console.log('Usage: node batch_download.js <url> <outputDir> [limit]');
    process.exit(1);
}

// Try to load .env from current or parent directories
let currentDir = process.cwd();
let envPath = path.join(currentDir, '.env');
let attempts = 0;
while (!fs.existsSync(envPath) && attempts < 5) {
    currentDir = path.dirname(currentDir);
    envPath = path.join(currentDir, '.env');
    attempts++;
}

if (fs.existsSync(envPath)) {
    console.log(`Loading .env from ${envPath}`);
    let envContent;
    const buf = fs.readFileSync(envPath);
    // Rough check for UTF-16LE
    if (buf[0] === 0xff && buf[1] === 0xfe) {
        envContent = buf.toString('utf16le');
    } else {
        envContent = buf.toString('utf8');
    }

    envContent.split(/\r?\n/).forEach(line => {
        const trimmed = line.trim();
        if (!trimmed || trimmed.startsWith('#')) return;
        const match = trimmed.match(/^([^=]+)=(.*)$/);
        if (match) {
            const key = match[1].trim();
            const value = match[2].trim().replace(/^['"](.*)['"]$/, '$1');
            if (key) {
                process.env[key] = value;
            }
        }
    });
}

const apiKey = process.env.FIRECRAWL_API_KEY;
if (!apiKey) {
    console.error('Error: FIRECRAWL_API_KEY environment variable is not set. Please assume .env file is in the project root.');
    process.exit(1);
}

async function run() {
    try {
        console.log(`Mapping URLs for ${rootUrl}...`);
        const mapCmd = `firecrawl map ${rootUrl} --limit ${limit}`;
        const mapOutput = execSync(mapCmd, { env: process.env }).toString();
        const urls = mapOutput.split('\n')
            .map(u => u.trim())
            .filter(u => u && u.startsWith('http') && !u.includes('?hl='));

        console.log(`Found ${urls.length} target URLs. Starting download...`);

        if (!fs.existsSync(outputBaseDir)) {
            fs.mkdirSync(outputBaseDir, { recursive: true });
        }

        for (const url of urls) {
            try {
                const urlObj = new URL(url);
                let filename = urlObj.pathname.replace(/^\/docs\//, '').replace(/\//g, '_') || 'index';
                if (!filename || filename === '/') filename = 'index';
                filename = filename.replace(/^_/, '');
                const filePath = path.join(outputBaseDir, `${filename}.md`);

                if (fs.existsSync(filePath)) {
                    console.log(`Skipping (already exists): ${url}`);
                    continue;
                }

                console.log(`Scraping: ${url} -> ${filePath}`);
                const scrapeCmd = `firecrawl scrape ${url} markdown`;
                const markdown = execSync(scrapeCmd, { env: process.env }).toString();

                fs.writeFileSync(filePath, markdown);
            } catch (e) {
                console.error(`Failed to scrape ${url}:`, e.message);
            }
        }
        console.log('Batch download completed.');
    } catch (e) {
        console.error('Error:', e.message);
    }
}

run();
