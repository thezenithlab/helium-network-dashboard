# Helium Network Research Dashboard

Interactive, self-contained web dashboard summarizing the Helium decentralized wireless network — built as a companion artifact to ongoing HICSS-58 extension research on Helium's post-Solana-migration economic and governance dynamics.

**Authors:** Pouria Rad · Mohsen Jozani · Gianluca Zanella (Zenith Lab, Augusta University)
**Data snapshot:** 2026-04-20 · **Coverage:** 2021-01-01 → 2026-04-20 (1,936 daily rows × 55 columns)
**Source paper:** Rad, P., Jozani, M., Zanella, G., Safaei Pour, M., & Abhari, K. (2025). *Reimagining the Sharing Economy through Blockchain: The Case of Helium's Decentralized Wireless Network.* Proceedings of HICSS-58.

---

## What this is

A single-page, Plotly.js + Leaflet dashboard rendering the full master time-series and geographic coverage of the Helium IoT (LoRaWAN) + Mobile (5G CBRS) network. Designed for:

- **Research transparency** — every chart caption documents source + operational definition
- **Co-author / reviewer access** — runs locally with one command, no build step
- **Demo / talk material** — pre-rendered for offline display

All data is pre-baked into two JSON files; the page is fully static once loaded.

---

## Quick start

The dashboard needs only Python 3 (already on every Mac/Linux). No Node, no npm, no build.

```bash
git clone https://github.com/thezenithlab/helium-network-dashboard.git
cd helium-network-dashboard
python3 -m http.server 8080
open http://localhost:8080
```

Or with Docker:

```bash
docker build -t helium-dashboard .
docker run --rm -p 8080:80 helium-dashboard
```

---

## What's in the repo

| File | Size | Purpose |
|------|------|---------|
| `index.html` | ~50 KB | Plotly + Leaflet SPA — all tabs and charts |
| `data.json` | ~810 KB | Daily time-series, derived series, correlation matrix |
| `coverage.json` | ~3.2 MB | H3 tile coverage (176,968 tiles) for the Map tab |
| `generate_data.py` | — | Rebuilds `data.json` from the master CSV (research-side only) |
| `Dockerfile` | — | Nginx-based static-serve image |

---

## Dashboard tabs

| Tab | Contents |
|-----|----------|
| **Prices** | HNT, BTC, IOT, MOBILE daily OHLCV · 7-day MA · normalized performance · 30-day rolling volatility |
| **Network** | DC burns/day with 7 & 30-day MA · cumulative burns · subDAO split · day-of-week pattern |
| **Hotspots** | Pre-Solana: daily creations, deaths, net change, owner count (HICSS V6 source) · Post-Solana: 5G radio onboardings + IoT oracle trend |
| **Mobile** | Subscribers vs 5G radio deployment · daily data (TB) · treasury balance · 30-day growth rate |
| **Correlation** | Pairwise Pearson heatmap + 3 scatter charts color-coded by year (click a legend year to hide/show) |
| **Data Coverage** | Per-column completeness bar chart for all 55 master-dataset columns |
| **Map** | Interactive Leaflet map — IoT hotspot heatmap (green) + Mobile 5G circle markers (pink) |

UI niceties:
- ☀️ / 🌙 light/dark toggle in the header — preference persists in `localStorage`.
- Click any chart title for the full operational definition and data source description.
- Click a year label in any Correlation scatter legend to isolate pre- vs post-migration periods.

---

## Where the data comes from

The master CSV that feeds `data.json` is produced by a separate, private scraper repository (not included here). Sources and modules:

| Source | What it provides | Module |
|--------|------------------|--------|
| CryptoCompare | HNT/BTC full OHLCV 2021→today | `08_cryptocompare_history.py` |
| CoinGecko (free tier) | IOT/MOBILE token prices (rolling 365-day cap) | `01_coingecko.py` |
| Helium S3 metrics feed | Mobile subscribers + data traffic (rolling 182 days) | `04_helium_network_api.py` |
| Helium Oracle | Active IoT/Mobile device snapshots (point-in-time) | `04_helium_network_api.py` |
| Dune Analytics | DC burned by subDAO, MOBILE treasury, subscriber NFTs | `02_dune_api.py` |
| Solana RPC (Helius) | Daily DC burn tx counts, full-history hotspot/radio onboarding via entity manager program | `09_solana_dc_burns.py`, `12_solana_entity_scan.py` |
| HeliumGeek PBF tiles | H3 → lat/lng for ~177k gateways | `11_gateway_locations.py` |
| HICSS V6 research dataset | Pre-Solana daily creations, deaths, owners, tx counts (2021-01-01 → 2023-04-18) | `13_hicss_presolana.py` |

The Solana migration (April 18, 2023) splits the dataset into two regimes — a `migration_flag` column marks the break.

---

## Rebuilding `data.json` (researchers only)

Requires access to the upstream scraper repo and a populated `data/processed/helium_daily_master.csv`. From the scraper root:

```bash
python dashboard/generate_data.py
# emits dashboard/data.json from the master CSV
```

Then `cp` the result over the version in this repo and commit.

---

## Known data limitations

These are inherent to the upstream sources, not bugs in this dashboard:

| Limitation | Why |
|---|---|
| **Post-Solana hotspot deaths** ≈ no data | Helium entity manager records onboarding instructions only — no on-chain deactivation event exists. Current proxy: oracle `active_iot_devices` snapshot deltas (small N today; grows daily). |
| **IOT/MOBILE token prices** ≈ ~20% coverage | Free-tier API caps history at 365 days. Manual CoinMarketCap export can extend. |
| **DC subDAO burn split** ≈ 3% coverage | Dune free-tier caches a rolling 30-day window. |
| **Mobile subscriber pre-2025-Jul** ≈ no data | Helium S3 feed serves only the rolling last 182 days. |
| **Pre-2021 history** | HICSS V6 source begins 2021-01-01. The Helium L1 stats API is retired; only Wayback Machine snapshots remain. |

A full per-column coverage table is rendered on the **Data Coverage** tab.

---

## Citation

If this dashboard or its underlying dataset is useful in your work, please cite:

> Rad, P., Jozani, M., Zanella, G., Safaei Pour, M., & Abhari, K. (2025). Reimagining the Sharing Economy through Blockchain: The Case of Helium's Decentralized Wireless Network. *Proceedings of the 58th Hawaii International Conference on System Sciences (HICSS-58).*

---

## Repository status

Private working artifact of the Zenith Lab (Augusta University). Not licensed for redistribution outside the project team without prior agreement.
