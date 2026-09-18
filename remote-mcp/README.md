## Deployment update: 18 September 2026

The remote MCP endpoint and connection guides are now published:

- MCP endpoint: `https://vnish.global/ai/mcp/index.php`
- [English connection guide](https://vnish.global/ai/connect/)
- [Русская инструкция подключения](https://vnish.global/ru/ai/connect/)

Public HTTPS verification with the official MCP JavaScript SDK 1.30.0 passed all 7 checks: PHP execution, protocol initialization, tool listing, resource access and one call to each of the three read-only tools. The negotiated protocol was `2025-11-25`. The two guide files, their stylesheet and the catalog snapshot matched the prepared release by SHA-256 and byte count.

Connection inside native ChatGPT and Claude accounts has not been tested. This result does not claim app-directory approval or physical miner testing.

**The original pre-deployment snapshot is preserved unchanged below. Its planned-publication wording records the earlier state.**

---

# VNISH Global Operator remote MCP

**Status: NOT YET DEPLOYED.** This is a reviewed source package and deployment candidate. The HTTPS endpoint and new connection-guide URLs below are planned. This README does not claim that ChatGPT or Claude has connected to the service or approved a directory listing.

The PHP server exposes three read-only tools using public VNISH Global catalog metadata, selected VNISH Ninja references and an ROI ASIC arithmetic scenario. It does not connect to miners, install firmware, run commands, fetch arbitrary URLs, use credentials or store tool arguments. Existing Operator skills and earlier MCP implementations are preserved.

## Files and deployment

The six files under `public/` are an additive deployment for **vnish.global**:

| File | Purpose |
| --- | --- |
| `ai/mcp/index.php` | Streamable HTTP endpoint |
| `ai/mcp/catalog-snapshot.json` | Dated public catalog snapshot |
| `ai/mcp/.htaccess` | `DirectoryIndex index.php` in this new directory only |
| `ai/connect/index.html` | English connection guide |
| `ai/connect/connect.css` | Isolated guide styles |
| `ru/ai/connect/index.html` | Russian connection guide |

Planned endpoint: `https://vnish.global/ai/mcp/index.php`.

Planned guides: `https://vnish.global/ai/connect/` and `https://vnish.global/ru/ai/connect/`.

Deploy only `public/` paths, after checking for existing files. Verify PHP execution and POST behavior on the hosting runtime. No existing site root, shared navigation, styles, JavaScript, sitemap, robots or security configuration is part of this package. GET and DELETE on the MCP endpoint return 405; connection guides are separate HTML pages. Test and data-source files do not belong in the web root.

## Tools

- `lookup_firmware`: exact catalog model ID, with optional board code and version. Returns filename, size, SHA-256 and Global source URLs. Multiple matching records stay ambiguous. A catalog record is not evidence of compatibility, authenticity or successful hardware testing.
- `find_ninja_reference`: fixed EN/RU guides for control-board identification, installation SSH errors and return-to-stock preparation. It does not determine whether a recovery method applies to a particular device.
- `calculate_roi_scenario`: gross pre-fee hashrate, average wall power, modeled fee, gross daily hashprice, electricity tariff and operating hours. All inputs are supplied by the caller. Both revenue and energy scale by the same operating-hours assumption. The output is contribution after the modeled fee and electricity, excluding other expenses; it is not net profit, ROI or a forecast.

The server also exposes three resources: the model ID index, snapshot provenance and scenario methodology. Resource URIs are identifiers used with MCP `resources/read`, not promised web pages.

## Data and boundaries

`data/source-catalog.json` is a copy of the public catalog at `https://vnish.global/api/v1/firmware-catalog.json`. `data/catalog-provenance.json` records its retrieval timestamp and SHA-256. The bundled snapshot contains 47 models and 148 build records. A snapshot is not a live availability check. No scheduled update process is included.

Selected identifiers and scenario numbers are sent to the server. Application code does not persist arguments; standard hosting/CDN logs may record request metadata. Passwords, account data, miner addresses and configuration files are unnecessary.

Protocol versions: `2026-07-28`, `2025-11-25`, `2025-06-18`, `2025-03-26`. Modern requests use `server/discover`, per-request metadata and mirrored headers. Legacy clients use `initialize`. The server creates no session ID and returns JSON instead of SSE. It provides no subscriptions, elicitation, sampling, batch requests or device operations.

Present Origin headers must exactly match the three project domains, `https://chatgpt.com` or `https://claude.ai`; absent Origin is permitted for server clients. Inputs are bounded to 32 KiB and depth 32. IDs must be strings or numbers whose integer value is in the safe range from -(2^53-1) to 2^53-1, so request correlation cannot be silently rounded.

## Reproduce tests

Requirements: Node.js 20.10 or newer; Python 3.9 or newer for builders. Runtime PHP hosting is separate from the test dependencies.

Pinned test dependencies:

- `@php-wasm/universal` 3.1.54
- `@php-wasm/node-8-4` 3.1.54
- `@modelcontextprotocol/sdk` 1.30.0

A pnpm lockfile pins transitive dependencies. From this directory:

```sh
pnpm install --frozen-lockfile
pnpm test
```

The tests execute the actual endpoint in PHP 8.4 WebAssembly, then start a temporary HTTP bridge bound to `127.0.0.1` and call it with the official SDK's `StreamableHTTPClientTransport`. The bridge closes when testing finishes. Tests cover tools, resources, current protocol metadata, origin validation, bounded inputs, scenario arithmetic, negative results and malformed/fractional/oversized request IDs. They need no production account, credentials or miner.

Generated receipts go in ignored `test-results/`. Tests do not access arbitrary network destinations; example invalid URLs are negative-test fixtures. No browser scripts or private QA artifacts are included.

Rebuild the public snapshot and guides from the bundled public source:

```sh
pnpm run build
```

A successful local test does not establish public hosting or an end-user client connection. After deployment, verify the public HTTPS endpoint and then test actual client connections.

## Links awaiting deployment

The connection pages' canonical/language URLs, their local `connect.css`, and the displayed MCP URL will work only after the `public/` files are published. Guide links to the current public catalog, existing Ninja and ROI ASIC references, official setup documentation and the existing Operator repository are independent of that deployment. The repository link deliberately points to the existing repository root until this package is published.

## Protocol and client documentation

- [MCP 2026-07-28 Streamable HTTP](https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/streamable-http)
- [Versioning and compatibility](https://modelcontextprotocol.io/specification/2026-07-28/basic/versioning)
- [Discovery](https://modelcontextprotocol.io/specification/2026-07-28/server/discover)
- [Tools](https://modelcontextprotocol.io/specification/2026-07-28/server/tools)
- [Legacy Streamable HTTP](https://modelcontextprotocol.io/specification/2025-11-25/basic/transports)
- [OpenAI connection guide](https://developers.openai.com/plugins/deploy/connect-chatgpt)
- [Anthropic connection guide](https://support.claude.com/en/articles/11175166-get-started-with-custom-connectors-using-remote-mcp)

Setup guidance was checked against official documentation on 2026-09-17. Account and workspace policy can affect available connection options.
