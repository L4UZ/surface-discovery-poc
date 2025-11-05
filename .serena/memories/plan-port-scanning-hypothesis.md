# Plan: Port Scanning Feature (Stage 1.5)

## Hypothesis

Add dedicated port discovery stage between subdomain enumeration (Stage 1) and HTTP probing (Stage 2) to discover open ports and services on discovered subdomains.

## Architecture Decision

### Stage Integration
**Chosen**: Stage 1.5 (Port Discovery) - Dedicated stage after passive discovery
**Rationale**:
- Better separation of concerns (network layer vs application layer)
- Can feed port results to HTTP probing for more efficient scanning
- Clear timeline events and progress tracking
- Optional: Can skip if time-constrained

### Data Model Design
**Approach**: Extend `Subdomain` model with `open_ports: List[PortScanResult]`
**Rationale**:
- Ports belong to specific subdomains/IPs
- Keeps data normalized and easy to query
- Natural fit with existing data structure

### Port Scanning Tool
**Tool**: naabu (already installed in Docker, capabilities configured)
**Advantages**:
- Fast SYN scan (uses raw packets)
- JSON output support
- Service detection capability
- Already integrated in ProjectDiscovery suite

## Expected Outcomes

### Performance Targets
- **Shallow depth**: +10-15s (top 100 ports)
- **Normal depth**: +30-60s (top 1000 ports)
- **Deep depth**: +2-5min (full 65535 ports)

### Data Quality
- Port accuracy: >95% (naabu is reliable)
- Service detection: Best-effort (naabu service probing)
- Coverage: All discovered subdomains with resolved IPs

### Statistics Enhancement
- `total_ports_scanned`: Total ports checked
- `open_ports_found`: Total open ports discovered
- `ports_by_subdomain`: Distribution metrics
- `common_services`: Most frequent services detected

## Configuration Design

### Depth-Based Port Limits
```python
DEPTH_CONFIGS = {
    "shallow": {
        "port_range": "top-100",  # --top-ports 100
        "naabu_timeout": 90,      # 1.5 minutes
        "port_rate": 1000         # packets/second
    },
    "normal": {
        "port_range": "top-1000", # --top-ports 1000
        "naabu_timeout": 180,     # 3 minutes
        "port_rate": 1500
    },
    "deep": {
        "port_range": "full",     # -p - (all ports)
        "naabu_timeout": 300,     # 5 minutes
        "port_rate": 2000
    }
}
```

### DiscoveryConfig Extensions
```python
# Port scanning settings
naabu_timeout: int = 180
port_scan_rate: int = 1500
max_ports_per_host: Optional[int] = None  # None = depth-based default
```

## Data Models

### PortScanResult
```python
class PortScanResult(BaseModel):
    port: int
    protocol: str = "tcp"  # tcp or udp
    state: str             # open, closed, filtered
    service: Optional[str] = None   # http, ssh, mysql, etc.
    version: Optional[str] = None   # service version if detected
    discovered_at: datetime
```

### Subdomain Extension
```python
class Subdomain(BaseModel):
    # ... existing fields ...
    open_ports: List[PortScanResult] = Field(default_factory=list)
    total_ports_scanned: int = 0
    open_ports_count: int = 0
```

## Implementation Phases

### Phase 1: Data Models (30 min)
1. Create `PortScanResult` model in `discovery/models/domain.py`
2. Extend `Subdomain` model with port fields
3. Update `__all__` exports

### Phase 2: Tool Integration (45 min)
1. Add `run_naabu()` to `ToolRunner` class
2. Handle JSON output parsing
3. Error handling and timeout management

### Phase 3: Stage Implementation (1 hour)
1. Create `discovery/stages/port_discovery.py`
2. Implement `PortDiscovery` class
3. Parse naabu output to `PortScanResult` objects
4. Update subdomain objects with port data

### Phase 4: Configuration (30 min)
1. Add port scanning config to `DiscoveryConfig`
2. Update depth presets with port ranges
3. Add to `DEPTH_CONFIGS` dictionary

### Phase 5: Pipeline Integration (45 min)
1. Add Stage 1.5 to `core.py` discovery pipeline
2. Insert between Stage 1 and Stage 2
3. Add timeline events
4. Update statistics calculation

### Phase 6: Testing (1 hour)
1. Test shallow depth (top 100 ports)
2. Test normal depth (top 1000 ports)
3. Test deep depth (full scan)
4. Verify JSON output structure
5. Validate statistics accuracy

## Success Criteria

✅ **Functional**:
- Port scanning completes for all subdomains with IPs
- Open ports correctly stored in Subdomain.open_ports
- Statistics accurately reflect port scan results

✅ **Performance**:
- Shallow: <15s additional time
- Normal: <60s additional time
- Deep: <5min additional time

✅ **Quality**:
- No crashes or unhandled exceptions
- Proper error handling for unreachable hosts
- Clean JSON output with port data
