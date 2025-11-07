# DNS Resolution Diagnostic Logging - 2025-01-06

## Problem Summary

**New Symptom After Timeout Fix**: Port discovery reports "0 hosts scanned" despite passive discovery finding 20 subdomains.

```
[22:03:40] INFO Passive discovery complete: 20 subdomains
[22:03:41] INFO Port discovery complete: 0 open ports found across 0 hosts
```

**Time Analysis**: Port discovery completes in 1 second (impossible for actual scanning) → indicates scan never executed.

## Root Cause

**Filter Logic**: Port discovery filters subdomains by IP resolution:
```python
# discovery/stages/port_discovery.py:48
scannable_subdomains = [sub for sub in subdomains if sub.ips]
```

**Problem**: All 20 subdomains have `ips=[]` (empty list), causing them all to be filtered out.

**Why IPs are empty**:
1. DNS resolution happens in passive discovery stage
2. `dnsx` might be failing or returning empty results
3. **No INFO-level logging** to show DNS resolution results to users
4. Silent failure → invisible problem

## Implemented Diagnostic Logging

### Fix 1: Passive Discovery DNS Resolution Logging ✅
**File**: `discovery/stages/passive.py:161-169`

Added INFO-level logging for DNS resolution process:

```python
# Before subdomain resolution
logger.info(f"Resolving {len(subdomains)} subdomains to IP addresses...")

# After DNS resolution
logger.info(f"DNS resolution complete: {len(subdomain_dns_data)}/{len(subdomains)} subdomains returned records")
```

### Fix 2: Passive Discovery IP Statistics ✅
**File**: `discovery/stages/passive.py:285-292`

Added logging to show how many subdomains successfully resolved to IPs:

```python
# Count resolved subdomains
resolved_count = 0
for subdomain_name in results.subdomains:
    dns_records = results.dns_records.get(subdomain_name)
    ips = []
    if dns_records:
        ips.extend(dns_records.a)
        ips.extend(dns_records.aaaa)
        if ips:
            resolved_count += 1

# Log IP resolution statistics
logger.info(
    f"DNS resolution: {resolved_count}/{len(subdomain_objects)} subdomains resolved to IPs"
)
if resolved_count == 0:
    logger.warning(
        "No subdomains resolved to IP addresses - port scanning and active discovery will be skipped"
    )
```

### Fix 3: Port Discovery Filter Logging ✅
**File**: `discovery/stages/port_discovery.py:47-60`

Added logging to show subdomain filtering:

```python
# Filter subdomains that have IP addresses
scannable_subdomains = [sub for sub in subdomains if sub.ips]
filtered_out = len(subdomains) - len(scannable_subdomains)

if filtered_out > 0:
    logger.warning(
        f"Filtered out {filtered_out}/{len(subdomains)} subdomains with no resolved IPs"
    )

if not scannable_subdomains:
    logger.warning(
        "No subdomains with resolved IPs to scan - skipping port discovery"
    )
    return results
```

## Expected Output After Fix

### Normal Scenario (DNS working)
```
[INFO] Passive discovery complete: 20 subdomains
[INFO] Resolving 20 subdomains to IP addresses...
[INFO] DNS resolution complete: 18/20 subdomains returned records
[INFO] DNS resolution: 18/20 subdomains resolved to IPs
[INFO] Stage 1.5: Port Discovery
[WARNING] Filtered out 2/20 subdomains with no resolved IPs
[INFO] Scanning 18 subdomains with resolved IPs
[INFO] Deep scan with 18 hosts: using full port range (65535)
[INFO] Deep port scan starting: 18 hosts, estimated time: 7.8 minutes
```

### Problem Scenario (DNS failing)
```
[INFO] Passive discovery complete: 20 subdomains
[INFO] Resolving 20 subdomains to IP addresses...
[INFO] DNS resolution complete: 0/20 subdomains returned records
[WARNING] No subdomains resolved to IP addresses - port scanning and active discovery will be skipped
[INFO] DNS resolution: 0/20 subdomains resolved to IPs
[INFO] Stage 1.5: Port Discovery
[WARNING] Filtered out 20/20 subdomains with no resolved IPs
[WARNING] No subdomains with resolved IPs to scan - skipping port discovery
```

## Diagnostic Steps

When user reports "0 hosts scanned":

1. **Check DNS resolution logs** - Look for:
   - "Resolving X subdomains to IP addresses..."
   - "DNS resolution complete: Y/X subdomains returned records"

2. **If Y=0** (no records returned):
   - DNS resolution is failing
   - Possible causes:
     - dnsx tool not working
     - Network/DNS server issues
     - Invalid subdomain names
     - Rate limiting

3. **If Y>0 but still 0 hosts**:
   - DNS records returned but no A/AAAA records
   - Check if subdomains are CNAMEs only

4. **Verify dnsx is working**:
   ```bash
   docker run --rm --entrypoint dnsx surface-discovery:latest -version
   echo "google.com" | docker run --rm -i --entrypoint dnsx surface-discovery:latest -silent -json -a
   ```

## Files Modified

1. `discovery/stages/passive.py:161-169` - DNS resolution progress logging
2. `discovery/stages/passive.py:261-292` - IP resolution statistics
3. `discovery/stages/port_discovery.py:47-60` - Subdomain filtering logging

## Next Steps for User

1. **Rebuild Docker image** with diagnostic logging:
   ```bash
   docker build -t surface-discovery:latest .
   ```

2. **Run test scan** to see diagnostic output:
   ```bash
   docker run --rm \
     --cap-add=NET_RAW --cap-add=NET_ADMIN \
     -v $(pwd)/results:/output \
     surface-discovery:latest \
     --url https://portal.strike.sh \
     --depth deep \
     --timeout 1800 \
     --output /output/diagnostic-scan.json
   ```

3. **Look for DNS resolution logs** in output:
   - Should show "Resolving X subdomains..."
   - Should show "DNS resolution complete: Y/X..."
   - Should show "DNS resolution: Z/X subdomains resolved to IPs"

4. **Report findings**:
   - If Y=0: DNS resolution completely failing
   - If Y>0 but Z=0: DNS returns records but no IPs
   - If Z>0: Success, port scanning should proceed

## Hypothesis

Most likely scenario: **dnsx is failing silently** due to:
- Missing DNS resolver configuration in Docker
- Network isolation in Docker
- dnsx tool permissions or capabilities

Less likely: Subdomains exist but don't have A/AAAA records (would be unusual for 20/20 subdomains).

## Related Issues

This diagnostic logging complements the timeout fix from earlier today. Together they provide:
1. Timeout visibility (from previous fix)
2. DNS resolution visibility (this fix)
3. Filtering visibility (this fix)

These logs will make it much easier to diagnose why scans fail.
