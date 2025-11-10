# TODO

## Features
- [ ] Add crawlee/playwright for deep link discovery on SPAs and web applications
- [ ] Test authenticated scans with real targets
- [ ] Improve authenticated discovery: discover new URLs found during auth crawling
- [ ] Group endpoints by subdomain in output
- [ ] Add rate limiting for API requests
- [ ] Add progressive saving and resume capability (Zod validation for state)
- [ ] Add TypeScript queue system for parallel operations

## Scanning Options
- [ ] Add flag to scan only a specific subdomain (not full root domain)
- [ ] Add VPN/private network access methods support

## Output Enhancements
- [ ] Add grooming step: separate JavaScript files from URLs
- [ ] Scan JavaScript files for sensitive data (research Node.js tools)
- [x] Flag URLs as public vs authentication-required

## API/Integration
- [ ] APIfication: Expose scan endpoint
- [ ] Stream results via WebSocket
- [ ] Add nmap-cli output format for naabu?

## Completed/Removed
- [x] Remove nuclei scanning (REMOVED in Node.js version)
- [x] Use modern package manager (using pnpm, Python used uv)
