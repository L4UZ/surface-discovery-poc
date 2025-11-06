# TODO

- [ ] Add crawlee to perform deep link discovery on single page apps and other web applications.
- [ ] Test authenticated scans
- [ ] If the input is a subdomain instead of a root domain, add a flag to only scan the subdomain.
- [ ] Improve authenticated scans so that any new urls (in the domain or not) are further discovered with the authentication method.
- [ ] Add a way to use a VPN or other access methods to access a "private" network. Suggest a list of most common access methods I should implement.
- [ ] Group endpoints by subdomain
- [ ] APIfication of the project.
  - [ ] Expose an endpoint to scan a url.
  - [ ] Stream results to a web socket.
- [x] Add a flag to the results, identifying if the url is publicly accessible or requires authentication.
- [ ] Add `-nmap-cli` to naabu?
- [ ] Add rate limiting
- [ ] Remove nuclei scanning from the project.
- [ ] Add progressive saving and the ability to resume from a saved state.
- [ ] Add queueing system?
- [ ] Add a grooming step:
  - [ ] Separate javascript files and other files from the found urls
- [ ] Scan javascript files for sensitive data. Research tools to do this.
- [ ] Use uv for package management
<!-- - [ ] Store metadata for the url, such as path params, query params, etc. -->
