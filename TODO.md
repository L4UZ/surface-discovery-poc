# TODO

- [x] Port scanning
- [ ] Migrate to AI agent framework providing it with tools to do the work.
- [ ] Test authenticated scans
- [ ] Improve authenticated scans so that any new urls (in the domain or not) are further discovered with the authentication method.
- [ ] Add a way to use a VPN or other access methods to access a "private" network. Suggest a list of most common access methods I should implement.
- [ ] Group endpoints by subdomain
- [ ] Add a flag to the results, identifying if the url is publicly accessible or requires authentication.
- [ ] Add `-nmap-cli` to naabu?
- [ ] Add rate limiting
- [ ] Remove nuclei scanning from the project.
- [ ] Add progressive saving and the ability to resume from a saved state.
- [ ] Add queueing system?
- [ ] Separate javascript files and other files from the found urls
- [ ] Scan javascript files for sensitive data. Research tools to do this.
- [ ] Use uv for package management
<!-- - [ ] Store metadata for the url, such as path params, query params, etc. -->
