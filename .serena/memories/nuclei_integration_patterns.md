# Nuclei Integration Patterns - Surface Discovery

## Overview
Nuclei is a template-based vulnerability scanner from ProjectDiscovery integrated into Stage 5 (Vulnerability Scanning) of the discovery pipeline.

## Critical Configuration

### Output Format
**CRITICAL**: Use `-jsonl` (JSON Lines) NOT `-json`
```python
# CORRECT
command = ['nuclei', '-silent', '-jsonl']

# WRONG - causes JSON parsing errors
command = ['nuclei', '-silent', '-json']
```

**Reason**: 
- `-json` returns single JSON object (empty when no findings)
- `-jsonl` returns one JSON object per line (JSONL format)
- Code uses line-by-line parsing: `for line in output.strip().split('\n')`

### Template Tags
Always pass template tags for targeted scanning:
```python
tags = [
    'cve',              # CVE-based vulnerabilities
    'exposure',         # Information exposure
    'misconfig',        # Misconfigurations
    'auth-bypass',      # Authentication bypasses
    'sqli',             # SQL injection
    'xss',              # Cross-site scripting
    'lfi',              # Local file inclusion
    'rce',              # Remote code execution
    'ssrf',             # Server-side request forgery
    'redirect',         # Open redirects
    'xxe',              # XML external entity
]

# Pass to nuclei
command.extend(['-tags', ','.join(tags)])
```

### Severity Filtering
Filter by severity levels (default: critical, high, medium):
```python
severity = ['critical', 'high', 'medium']
command.extend(['-severity', ','.join(severity)])
```

## Function Signature
```python
async def run_nuclei(
    self,
    targets: List[str],
    templates: Optional[List[str]] = None,
    tags: Optional[List[str]] = None,        # Must include this parameter
    severity: Optional[List[str]] = None,
    timeout: Optional[int] = None
) -> str:
```

## Target Preparation
```python
def _prepare_targets(services, endpoints):
    targets = set()
    
    # Add service base URLs
    for service in services:
        targets.add(service.url)
    
    # Add unique endpoint paths (deduplicate query params)
    unique_paths = set()
    for endpoint in endpoints:
        base_url = endpoint.url.split('?')[0]
        if base_url not in unique_paths:
            targets.add(endpoint.url)
            unique_paths.add(base_url)
    
    return list(targets)
```

## Output Parsing

### Empty Output Handling
**CRITICAL**: Check for empty output before parsing
```python
output = await self.runner.run_nuclei(...)

# MUST check for empty output
if not output or not output.strip():
    logger.debug("Nuclei returned no output (no vulnerabilities found)")
    return findings

# Then parse JSONL
for line in output.strip().split('\n'):
    if not line or not line.strip():  # Skip empty lines
        continue
    
    try:
        data = json.loads(line)
        finding = self._parse_nuclei_result(data)
        if finding:
            findings.append(finding)
    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse nuclei JSON line: {e}")
        logger.debug(f"Problematic line: {line[:100]}")  # Debug logging
        continue  # Continue processing other lines
```

### Result Parsing
```python
def _parse_nuclei_result(data):
    # Extract template info
    template_info = data.get('info', {})
    template_id = data.get('template-id', 'unknown')
    name = template_info.get('name', template_id)
    description = template_info.get('description', '')
    severity = template_info.get('severity', 'info')
    
    # Extract matched URL
    matched_at = data.get('matched-at') or data.get('host')
    if not matched_at:
        return None
    
    # Extract CVE references
    cve_refs = []
    classification = template_info.get('classification', {})
    if 'cve-id' in classification:
        cve_ids = classification['cve-id']
        if isinstance(cve_ids, list):
            for cve_id in cve_ids:
                cve_refs.append(CVE(id=cve_id, cvss_score=None))
        else:
            cve_refs.append(CVE(id=cve_ids, cvss_score=None))
    
    # Extract CWE
    cwe = classification.get('cwe-id')
    
    # Build evidence
    evidence = {
        'template_id': template_id,
        'matcher': data.get('matcher-name', ''),
        'extracted': data.get('extracted-results', [])
    }
    
    # Create Finding
    return Finding(
        title=name,
        description=description,
        severity=severity,
        url=matched_at,
        evidence=evidence,
        cve_references=cve_refs if cve_refs else None,
        cwe_id=cwe,
        discovered_at=datetime.utcnow(),
        tool='nuclei'
    )
```

## Error Handling Patterns

### Common Errors
1. **JSON Parsing Error**: `Expecting value: line 1 column 1`
   - Cause: Wrong flag (`-json` instead of `-jsonl`) or empty output
   - Fix: Use `-jsonl` and check for empty output

2. **Nuclei Execution Failed**: Empty error message
   - Causes: Template download failure, resource constraints, network issues
   - Solution: Check Docker network access, ensure sufficient resources

3. **Missing Findings**: Tags not applied
   - Cause: Tags parameter not passed to run_nuclei()
   - Fix: Ensure tags are included in function signature and command building

### Defensive Coding
```python
try:
    output = await self.runner.run_nuclei(
        targets=targets,
        templates=None,
        tags=tags,  # CRITICAL: Don't forget tags
        severity=severity,
        timeout=timeout
    )
    
    # CRITICAL: Handle empty output
    if not output or not output.strip():
        return findings
    
    # Parse with error handling
    for line in output.strip().split('\n'):
        if not line or not line.strip():
            continue
        
        try:
            data = json.loads(line)
            finding = self._parse_nuclei_result(data)
            if finding:
                findings.append(finding)
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse: {e}")
            continue  # Don't fail entire scan for one bad line
            
except Exception as e:
    logger.error(f"Nuclei execution failed: {e}")
    raise  # Re-raise for pipeline to handle
```

## Performance Considerations

### Timeouts
- Default: 180s (3 minutes)
- Can be extended via config: `nuclei_timeout` parameter
- Shallow depth: 60s may be sufficient
- Deep depth: 300s (5 minutes) recommended

### Target Limits
- Limit unique paths to avoid overwhelming nuclei
- Prioritize base URLs over query param variations
- Consider sampling for very large endpoint sets (>1000)

### Resource Usage
- Nuclei can be CPU and network intensive
- First run downloads templates (one-time cost)
- Subsequent runs use cached templates
- Consider --skip-vuln-scan flag for quick reconnaissance

## Toggle Feature

### CLI Flag
```bash
# Skip vulnerability scanning
python cli.py --url example.com --skip-vuln-scan

# Run with vulnerability scanning (default)
python cli.py --url example.com
```

### Implementation
```python
# In core.py
if not self.config.skip_vuln_scan:
    await self._run_vulnerability_scan()
else:
    logger.info("Stage 5: Vulnerability Scanning (skipped by --skip-vuln-scan flag)")
    self.result.add_timeline_event(
        DiscoveryStage.COMPLETED,
        "Vulnerability scanning skipped by user configuration"
    )
```

### Benefits
- 30-50% faster execution when vulnerabilities not needed
- Useful for quick reconnaissance or when time-constrained
- Still provides comprehensive discovery (stages 1-4)

## Best Practices

1. **Always use -jsonl flag** - Never use -json
2. **Always check empty output** - Before JSON parsing
3. **Always pass template tags** - For targeted scanning
4. **Always handle parse errors** - Continue processing other lines
5. **Always log problematic lines** - For debugging
6. **Consider skip flag** - For performance optimization
7. **Set appropriate timeouts** - Based on depth configuration
8. **Limit target count** - To avoid overwhelming scanner

## Common Pitfalls

❌ **Wrong**: Using `-json` flag
✅ **Correct**: Using `-jsonl` flag

❌ **Wrong**: Not checking for empty output
✅ **Correct**: Validating output before parsing

❌ **Wrong**: Preparing tags but not passing them
✅ **Correct**: Passing tags to run_nuclei()

❌ **Wrong**: Failing entire scan on one parse error
✅ **Correct**: Continue processing with warning

❌ **Wrong**: No timeout for long-running scans
✅ **Correct**: Set appropriate timeout based on depth
