# System Initialization Flow

## Boot sequence

1. Application entry point verifies Windows platform.
2. Process DPI awareness is applied when available.
3. Display and graphics services initialize lazily.
4. Display enumeration is executed before UI or report rendering.
5. Optional graphics refresh is triggered by lifecycle policy.

## Graphics initialization responsibilities

- Query display topology from Win32 APIs.
- Preserve active display mode properties during reapply operations.
- Use test-first mode application (`CDS_TEST`) before registry update commit.
- Commit all staged display changes once via global commit.

## Lifecycle events

The graphics lifecycle service supports these event types:

- `startup`: baseline stabilization after process launch.
- `wake`: post-sleep wake path revalidates active outputs.
- `manual_reset`: operator-triggered refresh via API/CLI.

## Safe re-init guardrails

- Inactive displays are ignored to avoid unintended enablement.
- Missing current-mode data causes display-level skip with warning.
- Failed display apply does not abort full batch; commit still executes for successful paths.
- Final success is based on global commit result.

## Operational edge cases

- A driver may report a display but with no current mode during transient wake states.
- Color depth support is device-specific; unsupported depth requests are skipped.
- Some adapters expose unusual orientation values; these map to `Unknown` when outside expected range.
