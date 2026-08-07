# Helium Network Research Dashboard

An open, interactive companion to our research on the Helium Network, a decentralized wireless
network built and operated by its participants rather than by a telecommunications firm.

The dashboard exists so that the empirical claims in our published work can be checked. Open the
**Paper Claims** tab and each claim appears with the figure as published, the source it came from,
what this dataset independently says about it, and a link to the chart that carries the evidence.
Where our data disagrees with a published figure, both are shown and the disagreement is explained.

**Live dashboard:** https://thezenithlab.github.io/helium-network-dashboard/

**Data:** 1,936 daily observations, 1 January 2021 to 20 April 2026, plus a global coverage
snapshot of 176,967 hexagonal tiles taken 7 April 2026.

---

## What is in it

| Tab | Contents |
|---|---|
| **Paper Claims** | Every empirical claim in the research, traced to the data, grouped by the pillar of the framework it supports |
| **Prices** | HNT, BTC, IOT and MOBILE daily prices, 7-day moving average, performance indexed to the Solana migration, 30-day rolling volatility |
| **Network** | Data Credit burns per day with 7 and 30-day moving averages, cumulative burns, subnetwork split, day-of-week pattern |
| **Hotspots** | Pre-Solana daily creations, deaths, net change and owner counts; post-Solana on-chain registrations |
| **Mobile** | Subscribers against 5G radio deployment, daily data carried, treasury balance, 30-day growth |
| **Correlation** | Pearson matrix over post-migration variables plus three scatter plots, filterable by year |
| **Data Coverage** | Per-column completeness for the whole dataset, and the operational definition of every chart |
| **Map** | Interactive world map, IoT coverage as a heatmap and Mobile 5G radios as points |

Hover or focus any chart title for its operational definition. All definitions are also reproduced
as selectable text at the bottom of the **Data Coverage** tab, since hover tooltips cannot be
reached on touch devices or copied into a citation.

## Running it locally

No build step, no Node, no npm. Any static file server works:

```bash
git clone https://github.com/thezenithlab/helium-network-dashboard.git
cd helium-network-dashboard
python3 -m http.server 8080
# then open http://localhost:8080
```

Or with Docker:

```bash
docker build -t helium-dashboard .
docker run --rm -p 8080:80 helium-dashboard
```

Opening `index.html` directly from the filesystem will not work: the page fetches its data over
HTTP. The charting and mapping libraries load from a CDN, so an internet connection is required.

## Where the data comes from

| Source | What it provides |
|---|---|
| CryptoCompare | HNT and BTC daily prices and volume, 2021 to present |
| CoinGecko | IOT and MOBILE token prices (free tier caps history at 365 days) |
| Helium public metrics feed | Mobile subscriber counts and data carried (rolling 182-day window) |
| Helium oracle endpoints | Active IoT and Mobile device counts (point-in-time snapshots) |
| Dune Analytics | Data Credits burned by subnetwork, MOBILE treasury, subscriber NFTs |
| Solana RPC | Daily Data Credit burn transactions, and full hotspot and radio onboarding history from the on-chain entity manager |
| HeliumGeek tile server | Hexagonal grid locations for approximately 177,000 gateways |
| Prior research dataset | Pre-Solana daily creations, deaths, owners and transaction counts, 1 Jan 2021 to 18 Apr 2023 |

Helium migrated from its own blockchain to Solana on **18 April 2023**. That date splits the
dataset into two measurement regimes, and a flag in the data marks the break. Several series
change basis at that point and are not directly comparable across it.

`generate_data.py` is included for transparency about how each series is derived. It reads a master
CSV produced by our collection pipeline, which is not part of this repository, so it will not run
as-is from a clone.

## Known limitations

These come from the upstream sources and are not defects in the dashboard. We keep sparse fields
rather than filling them with modelled values, so that what was actually observed stays auditable.

| Limitation | Why |
|---|---|
| **Hotspot deactivations after April 2023 are unrecoverable** | Helium's Solana entity manager records onboarding only. No deactivation instruction exists on chain. Post-migration counts are therefore cumulative registrations, not active devices, and the two differ by roughly a factor of four. |
| **Active device counts are two snapshots, not a series** | The oracle endpoints report a current count with no history. Treat them as point-in-time readings. |
| **IOT and MOBILE token prices cover about 20% of the window** | The free API tier caps history at 365 days. |
| **Data Credit burns split by subnetwork covers 24 days** | Those 24 days are consecutive and recent (late March to late April 2026), not spread across the window. |
| **Mobile subscriber data begins late 2025** | The metrics feed serves only a rolling 182-day window. Note that two different subscriber series exist and measure different things: one counts cumulative subscriber NFTs minted, the other is a rolling count from the metrics feed. They are labelled separately in the interface. |
| **Correlations are computed on levels** | Not on returns or first differences. Trending series correlate simply because both trend, so read the large positive coefficients as co-movement over time rather than as evidence of causation. |
| **Some series are the same signal under two names** | Where a column falls back to another source when its preferred input is absent, the result can duplicate an existing series. We remove known duplicates from the correlation matrix rather than letting them inflate it. |
| **The day-of-week chart is a null result** | Medians span about 3 percent across the week. It is kept for transparency, not because it shows a pattern. |

A full per-column completeness table is on the **Data Coverage** tab.

## Citing this

If the dashboard or its underlying dataset is useful in your work, please cite the source paper:

> Rad, P., Jozani, M., Zanella, G., Safaei Pour, M., & Abhari, K. (2025). Reimagining the Sharing
> Economy through Blockchain: The Case of Helium's Decentralized Wireless Network. *Proceedings of
> the 58th Hawaii International Conference on System Sciences (HICSS-58).*

## Licence

Code in this repository is released under the MIT Licence. The datasets (`data.json`,
`coverage.json`) are released under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/): use
and adapt them freely, with attribution. See `LICENSE`.

Data originates from third-party sources listed above and remains subject to those providers' own
terms. Nothing here is affiliated with or endorsed by Nova Labs or the Helium Foundation.

## Authors

Pouria Rad, Mohsen Jozani, Gianluca Zanella, Morteza Safaei Pour and Kaveh Abhari.
Zenith Lab, Augusta University, and San Diego State University.
