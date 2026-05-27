"""
Dashboard Data Generator
=========================
Reads the master CSV and produces a JSON file for the web dashboard.
Run this after 07_merge_master.py to refresh dashboard data.
"""
import json
import logging
import math
from pathlib import Path

import numpy as np
import pandas as pd


class _SafeEncoder(json.JSONEncoder):
    """Replace NaN/Infinity with None so the output is valid JSON."""
    def default(self, obj):
        if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
            return None
        return super().default(obj)

    def encode(self, o):
        return super().encode(self._sanitize(o))

    def _sanitize(self, o):
        if isinstance(o, float) and (math.isnan(o) or math.isinf(o)):
            return None
        if isinstance(o, dict):
            return {k: self._sanitize(v) for k, v in o.items()}
        if isinstance(o, (list, tuple)):
            return [self._sanitize(v) for v in o]
        return o

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(message)s")
log = logging.getLogger(__name__)

MASTER_CSV = Path(__file__).parent.parent / "data" / "processed" / "helium_daily_master.csv"
OUTPUT_JSON = Path(__file__).parent / "data.json"


def generate():
    df = pd.read_csv(MASTER_CSV)
    # Detect date column (could be 'date' or 'index')
    date_col = "date" if "date" in df.columns else "index"
    df[date_col] = pd.to_datetime(df[date_col])
    df = df.rename(columns={date_col: "date"})
    dup_days = int(df["date"].duplicated(keep=False).sum())
    if dup_days:
        log.warning(f"Found {dup_days} duplicate date rows in master; keeping last record per day for dashboard")
        df = df.drop_duplicates(subset=["date"], keep="last")
    df = df.sort_values("date")
    log.info(f"Loaded {len(df)} rows × {len(df.columns)} cols")

    # Validate/fix HNT 7-day MA against raw hnt_close.
    hnt_close7_mismatch_rows = 0
    if "hnt_close" in df.columns:
        df["HNT_Close7_validated"] = df["hnt_close"].rolling(7).mean()
        if "HNT_Close7" in df.columns:
            diff = (df["HNT_Close7"] - df["HNT_Close7_validated"]).abs()
            hnt_close7_mismatch_rows = int((diff > 1e-9).sum())
            if hnt_close7_mismatch_rows:
                log.warning(
                    f"HNT_Close7 mismatch detected on {hnt_close7_mismatch_rows} rows; "
                    "using validated rolling mean for dashboard output"
                )
        else:
            log.warning("HNT_Close7 missing in master; using validated rolling mean for dashboard output")

    # Convert dates to strings
    dates = df["date"].dt.strftime("%Y-%m-%d").tolist()

    # Helper to safely extract a column as list with NaN → None
    def col(name):
        if name not in df.columns:
            return None
        return df[name].where(df[name].notna(), None).tolist()

    # Unified hotspot count series from best available sources (priority order).
    hotspot_candidates = [
        "iot_cumulative_registered",
        "total_hotspots_v6",       # HICSS pre-Solana (highest pre-migration resolution)
        "total_hotspots",
        "iot_total_hotspots",
        "wayback_total_hotspots",
        "active_iot_devices",
    ]
    present_hotspot_cols = [c for c in hotspot_candidates if c in df.columns]
    if present_hotspot_cols:
        df["hotspots_registered"] = df[present_hotspot_cols[0]]
        for c in present_hotspot_cols[1:]:
            df["hotspots_registered"] = df["hotspots_registered"].fillna(df[c])

    # Calculate data coverage stats
    total_rows = len(df)
    coverage = {}
    for c in df.columns:
        if c == "date":
            continue
        n = df[c].notna().sum()
        coverage[c] = round(n / total_rows * 100, 1)

    # Summary statistics
    post_migration = df[df["migration_flag"] == 1] if "migration_flag" in df.columns else pd.DataFrame()

    summary = {
        "total_rows": total_rows,
        "date_range": f"{dates[0]} → {dates[-1]}",
        "total_columns": len(df.columns),
        "post_migration_rows": len(post_migration),
        "hnt_price_latest": round(df["hnt_close"].dropna().iloc[-1], 4) if "hnt_close" in df.columns and df["hnt_close"].notna().any() else None,
        "btc_price_latest": round(df["btc_close"].dropna().iloc[-1], 2) if "btc_close" in df.columns and df["btc_close"].notna().any() else None,
        "iot_devices_latest": int(df["active_iot_devices"].dropna().iloc[-1]) if "active_iot_devices" in df.columns and df["active_iot_devices"].notna().any() else None,
        "mobile_devices_latest": int(df["active_mobile_devices"].dropna().iloc[-1]) if "active_mobile_devices" in df.columns and df["active_mobile_devices"].notna().any() else None,
        "hotspots_registered_latest": int(df["hotspots_registered"].dropna().iloc[-1]) if "hotspots_registered" in df.columns and df["hotspots_registered"].notna().any() else None,
        "hnt_close7_validation_mismatches": hnt_close7_mismatch_rows,
        "dc_burns_total": int(df["dc_burn_tx_count"].sum()) if "dc_burn_tx_count" in df.columns else 0,
        "mobile_subscribers_latest": int(df["dune_mobile_subscribers"].dropna().iloc[-1]) if "dune_mobile_subscribers" in df.columns and df["dune_mobile_subscribers"].notna().any() else None,
        "mobile_radios_total": int(df["mobile_cumulative_registered"].dropna().iloc[-1]) if "mobile_cumulative_registered" in df.columns and df["mobile_cumulative_registered"].notna().any() else None,
    }

    # ── Derived series ────────────────────────────────────────────────────────
    # Price log-returns
    df["hnt_log_ret"] = np.log(df["hnt_close"] / df["hnt_close"].shift(1))
    df["btc_log_ret"] = np.log(df["btc_close"] / df["btc_close"].shift(1))
    # Annualized 30-day rolling volatility (%)
    df["hnt_vol30"] = df["hnt_log_ret"].rolling(30).std() * np.sqrt(365) * 100
    df["btc_vol30"] = df["btc_log_ret"].rolling(30).std() * np.sqrt(365) * 100
    # HNT price relative to BTC (normalized to BTC price units)
    df["hnt_btc_ratio"] = df["hnt_close"] / df["btc_close"]
    # HNT and BTC normalized to 1.0 at Solana migration date for relative comparison
    mig_date = "2023-04-18"
    mig_hnt = df.loc[df["date"] == mig_date, "hnt_close"]
    mig_btc = df.loc[df["date"] == mig_date, "btc_close"]
    if len(mig_hnt):
        df["hnt_norm_mig"] = df["hnt_close"] / float(mig_hnt.iloc[0])
        df["btc_norm_mig"] = df["btc_close"] / float(mig_btc.iloc[0])
    # DC burn 7/30-day moving averages
    if "dc_burn_tx_count" in df.columns:
        df["dc_burn_7ma"]  = df["dc_burn_tx_count"].rolling(7).mean()
        df["dc_burn_30ma"] = df["dc_burn_tx_count"].rolling(30).mean()
        df["dc_burn_cumulative"] = df["dc_burn_tx_count"].cumsum()
    # Mobile subscriber 30-day growth rate (%)
    if "dune_mobile_subscribers" in df.columns:
        df["mob_sub_30d_growth"] = df["dune_mobile_subscribers"].pct_change(30) * 100
    # Mobile data per subscriber (GB/subscriber)
    if "mobile_data_tb" in df.columns and "dune_mobile_subscribers" in df.columns:
        df["data_per_sub_gb"] = df["mobile_data_tb"] / df["dune_mobile_subscribers"] * 1000
    # Mobile radio vs subscriber ratio (radios per 1K subscribers)
    if "mobile_cumulative_registered" in df.columns and "dune_mobile_subscribers" in df.columns:
        df["radios_per_1k_subs"] = (
            df["mobile_cumulative_registered"] / df["dune_mobile_subscribers"] * 1000
        )
    # Day-of-week DC burn aggregate (for bar chart)
    if "dc_burn_tx_count" in df.columns and "DayOfWeek" in df.columns:
        dow_agg = df.groupby("DayOfWeek")["dc_burn_tx_count"].median().round(1)
        dow_labels = {1: "Mon", 2: "Tue", 3: "Wed", 4: "Thu", 5: "Fri", 6: "Sat", 7: "Sun"}
        dow_chart = {
            "labels": [dow_labels.get(int(k), str(k)) for k in dow_agg.index],
            "values": dow_agg.tolist(),
        }
    else:
        dow_chart = None

    # Build monthly aggregates for bar charts
    df["month"] = df["date"].dt.to_period("M").astype(str)
    monthly = df.groupby("month").agg({
        "dc_burn_tx_count": "sum",
        "hnt_close": "mean",
        "btc_close": "mean",
    }).reset_index()
    monthly = monthly.replace({np.nan: None})

    # Correlation matrix for key variables (post-migration only)
    # Use columns with sufficient post-migration coverage (>10 rows of overlap)
    corr_col_candidates = [
        "hnt_close", "btc_close", "dc_burn_tx_count",
        "daily_transaction_count", "hnt_volume", "iot_close", "mobile_close",
        "dune_mobile_subscribers", "mobile_data_tb",
    ]
    corr_cols = [c for c in corr_col_candidates if c in df.columns]
    if len(corr_cols) >= 2 and len(post_migration) > 30:
        corr_df = post_migration[corr_cols].dropna(how="all")
        # Only include columns that have at least 10 non-null values
        corr_cols_valid = [c for c in corr_cols if corr_df[c].notna().sum() >= 10]
        corr_df = corr_df[corr_cols_valid]
        corr = corr_df.corr().round(3)
        # Human-friendly axis labels
        label_map = {
            "hnt_close": "HNT Price",
            "btc_close": "BTC Price",
            "dc_burn_tx_count": "DC Burns/day",
            "daily_transaction_count": "Daily Txns",
            "hnt_volume": "HNT Volume",
            "iot_close": "IOT Price",
            "mobile_close": "MOBILE Price",
            "dune_mobile_subscribers": "Mobile Subs",
            "mobile_data_tb": "Mobile Data (TB)",
        }
        friendly_labels = [label_map.get(c, c) for c in corr.columns.tolist()]
        corr_matrix = {
            "labels": friendly_labels,
            "raw_labels": corr.columns.tolist(),
            "values": corr.values.tolist(),
        }
    else:
        corr_matrix = None

    data = {
        "generated_at": pd.Timestamp.now().isoformat(),
        "summary": summary,
        "coverage": coverage,
        "dates": dates,
        "series": {
            "hnt_close": col("hnt_close"),
            "hnt_volume": col("hnt_volume"),
            "hnt_volume_usd": col("hnt_volume_usd"),
            "btc_close": col("btc_close"),
            "iot_close": col("iot_close"),
            "mobile_close": col("mobile_close"),
            "dc_burn_tx_count": col("dc_burn_tx_count"),
            "daily_transaction_count": col("daily_transaction_count"),
            "total_hotspots": col("total_hotspots"),
            "hotspots_registered": col("hotspots_registered"),
            "iot_cumulative_registered": col("iot_cumulative_registered"),
            "wayback_total_hotspots": col("wayback_total_hotspots"),
            "active_iot_devices": col("active_iot_devices"),
            "active_mobile_devices": col("active_mobile_devices"),
            # HICSS pre-Solana hotspot vitals
            "daily_hotspot_creations": col("daily_hotspot_creations"),
            "daily_hotspot_deaths": col("daily_hotspot_deaths"),
            "daily_hotspot_net_change": col("daily_hotspot_net_change"),
            "total_hotspots_v6": col("total_hotspots_v6"),
            "total_hotspot_owners": col("total_hotspot_owners"),
            "hicss_daily_tx_count": col("hicss_daily_tx_count"),
            "mobile_subscribers": col("mobile_subscribers"),
            "dune_mobile_subscribers": col("dune_mobile_subscribers"),
            "mobile_data_tb": col("mobile_data_tb"),
            "mobile_treasury_balance": col("mobile_treasury_balance"),
            "iot_dc_burned": col("iot_dc_burned"),
            "mobile_dc_burned": col("mobile_dc_burned"),
            "migration_flag": col("migration_flag"),
            "HNT_Close7": col("HNT_Close7_validated") if "HNT_Close7_validated" in df.columns else col("HNT_Close7"),
            # Derived price series
            "hnt_vol30": col("hnt_vol30"),
            "btc_vol30": col("btc_vol30"),
            "hnt_btc_ratio": col("hnt_btc_ratio"),
            "hnt_norm_mig": col("hnt_norm_mig"),
            "btc_norm_mig": col("btc_norm_mig"),
            # Derived DC burn series
            "dc_burn_7ma": col("dc_burn_7ma"),
            "dc_burn_30ma": col("dc_burn_30ma"),
            "dc_burn_cumulative": col("dc_burn_cumulative"),
            # Derived mobile series
            "mob_sub_30d_growth": col("mob_sub_30d_growth"),
            "data_per_sub_gb": col("data_per_sub_gb"),
            "radios_per_1k_subs": col("radios_per_1k_subs"),
            # Post-Solana mobile radio deployments (hotspot creation proxy)
            "mobile_new_radios_onchain": col("mobile_new_radios_onchain"),
            "mobile_cumulative_registered": col("mobile_cumulative_registered"),
            "mobile_total_radios": col("mobile_total_radios"),
            "mobile_new_radios": col("mobile_new_radios"),
        },
        "monthly": {
            "months": monthly["month"].tolist(),
            "dc_burns": monthly["dc_burn_tx_count"].tolist(),
            "hnt_avg": monthly["hnt_close"].tolist(),
        },
        "dow": dow_chart,
        "correlation": corr_matrix,
    }

    OUTPUT_JSON.write_text(json.dumps(data, cls=_SafeEncoder, default=str))
    log.info(f"Dashboard data written: {OUTPUT_JSON} ({OUTPUT_JSON.stat().st_size / 1024:.0f} KB)")

    # ── Coverage map JSON ─────────────────────────────────────────────────────
    GATEWAY_CSV = Path(__file__).parent.parent / "data" / "raw" / "gateway_locations_latest.csv"
    COVERAGE_JSON = Path(__file__).parent / "coverage.json"
    if GATEWAY_CSV.exists():
        gdf = pd.read_csv(GATEWAY_CSV)
        gdf = gdf[(gdf["iot_count"] > 0) | (gdf["mobile_count"] > 0)].copy()
        gdf = gdf.dropna(subset=["lat", "lng"])
        # Use columnar arrays (much more compact than array-of-objects)
        # Round to 3 decimal places (~111m precision — sufficient for H3 res-8 tiles ~461m wide)
        coverage_out = {
            "scraped": gdf["date_scraped"].iloc[0] if "date_scraped" in gdf.columns else "unknown",
            "total_tiles": int(len(gdf)),
            "iot_tiles": int((gdf["iot_count"] > 0).sum()),
            "mobile_tiles": int((gdf["mobile_count"] > 0).sum()),
            # Columnar arrays for compact transfer
            "lats": [round(v, 3) for v in gdf["lat"].tolist()],
            "lngs": [round(v, 3) for v in gdf["lng"].tolist()],
            "iots": gdf["iot_count"].astype(int).tolist(),
            "mobs": gdf["mobile_count"].astype(int).tolist(),
        }
        COVERAGE_JSON.write_text(json.dumps(coverage_out, cls=_SafeEncoder, separators=(',', ':')))
        log.info(f"Coverage map data written: {COVERAGE_JSON} ({COVERAGE_JSON.stat().st_size / 1024:.0f} KB, {len(gdf):,} tiles)")
    else:
        log.warning(f"Gateway locations file not found: {GATEWAY_CSV}")


if __name__ == "__main__":
    generate()
