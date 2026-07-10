"""
Field-level data lineage tracker.

Maps how every column flows from ODS through DIM/DWD/DWS/DWT to ADS.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Lineage definitions — field provenance across warehouse layers
# ---------------------------------------------------------------------------

COMMENT_LINEAGE: dict[str, Any] = {
    "domain": "comment",
    "layers": {
        "ods": {
            "table": "ods_basiccomment_avatar_commentbatchsource_dic",
            "fields": {
                "id":          {"source": "MySQL.avatar_commentbatchsource.id",          "type": "bigint"},
                "batchnumber": {"source": "MySQL.avatar_commentbatchsource.batchnumber",  "type": "string"},
                "batchtype":   {"source": "MySQL.avatar_commentbatchsource.batchtype",    "type": "string"},
                "ctime":       {"source": "MySQL.avatar_commentbatchsource.ctime",        "type": "string"},
                "utime":       {"source": "MySQL.avatar_commentbatchsource.utime",        "type": "string"},
                "ver":         {"source": "MySQL.avatar_commentbatchsource.ver",          "type": "int"},
            },
        },
        "dwd": {
            "table": "dwd_comment_batch_detail_di",
            "downstream_of": ["ods_basiccomment_avatar_commentbatchsource_dic"],
            "fields": {
                "id":          {"source": "ods.id",          "transform": "direct"},
                "batchnumber": {"source": "ods.batchnumber", "transform": "direct"},
                "batchtype":   {"source": "ods.batchtype",   "transform": "direct"},
                "batchtype_name": {"source": "dim.dim_comment_batch_type.batchtype_name", "transform": "join_lookup"},
                "ctime":       {"source": "ods.ctime",       "transform": "direct"},
                "utime":       {"source": "ods.utime",       "transform": "direct"},
            },
        },
        "dws": {
            "table": "dws_comment_batch_1d",
            "downstream_of": ["dwd_comment_batch_detail_di"],
            "fields": {
                "batchtype":   {"source": "dwd.batchtype",   "transform": "group_by_key"},
                "batch_cnt":   {"source": "dwd.id",          "transform": "count"},
                "priority_batch_cnt": {"source": "dwd.batchtype", "transform": "conditional_count"},
            },
        },
        "dwt": {
            "table": "dwt_comment_batch_topic_td",
            "downstream_of": ["dws_comment_batch_1d", "dwt_comment_batch_topic_td(T-1)"],
            "fields": {
                "batchtype":         {"source": "dws.batchtype",           "transform": "coalesce_self_join"},
                "total_batch_cnt":   {"source": "dws.batch_cnt",           "transform": "cumulative_sum"},
                "priority_batch_cnt":{"source": "dws.priority_batch_cnt",  "transform": "cumulative_sum"},
                "latest_batch_time": {"source": "biz_dt",                  "transform": "literal"},
            },
        },
        "ads": {
            "table": "ads_comment_dashboard_1d",
            "downstream_of": ["dwt_comment_batch_topic_td"],
            "fields": {
                "metric_name":  {"source": "literal",     "transform": "derived"},
                "metric_value": {"source": "dwt.*",       "transform": "aggregate"},
            },
        },
    },
}

TRADE_LINEAGE: dict[str, Any] = {
    "domain": "trade",
    "layers": {
        "ods": {
            "table": "ods_trade_order_info_dic",
            "fields": {
                "id":           {"source": "MySQL.order_info.id",            "type": "bigint"},
                "user_id":      {"source": "MySQL.order_info.user_id",       "type": "bigint"},
                "order_no":     {"source": "MySQL.order_info.order_no",      "type": "string"},
                "pay_amount":   {"source": "MySQL.order_info.pay_amount",    "type": "double"},
                "order_status": {"source": "MySQL.order_info.order_status",  "type": "string"},
                "ctime":        {"source": "MySQL.order_info.ctime",         "type": "string"},
                "utime":        {"source": "MySQL.order_info.utime",         "type": "string"},
                "ver":          {"source": "MySQL.order_info.ver",           "type": "int"},
            },
        },
        "ods_user": {
            "table": "ods_user_user_info_dic",
            "fields": {
                "id":            {"source": "MySQL.user_info.id",            "type": "bigint"},
                "user_name":     {"source": "MySQL.user_info.user_name",     "type": "string"},
                "register_time": {"source": "MySQL.user_info.register_time", "type": "string"},
            },
        },
        "dwd": {
            "table": "dwd_trade_order_detail_di",
            "downstream_of": ["ods_trade_order_info_dic", "ods_user_user_info_dic"],
            "fields": {
                "order_id":     {"source": "ods_order.id",           "transform": "rename"},
                "user_id":      {"source": "ods_order.user_id",      "transform": "direct"},
                "order_no":     {"source": "ods_order.order_no",     "transform": "direct"},
                "pay_amount":   {"source": "ods_order.pay_amount",   "transform": "direct"},
                "order_status": {"source": "ods_order.order_status", "transform": "direct"},
                "user_name":    {"source": "ods_user.user_name",     "transform": "join_left"},
            },
        },
        "dws": {
            "table": "dws_trade_user_1d",
            "downstream_of": ["dwd_trade_order_detail_di"],
            "fields": {
                "user_id":    {"source": "dwd.user_id",    "transform": "group_by_key"},
                "order_cnt":  {"source": "dwd.order_id",   "transform": "count"},
                "pay_amount": {"source": "dwd.pay_amount", "transform": "sum"},
            },
        },
        "dwt": {
            "table": "dwt_trade_user_td",
            "downstream_of": ["dws_trade_user_1d", "dwt_trade_user_td(T-1)"],
            "fields": {
                "user_id":          {"source": "dws.user_id",          "transform": "coalesce_self_join"},
                "total_order_cnt":  {"source": "dws.order_cnt",        "transform": "cumulative_sum"},
                "total_pay_amount": {"source": "dws.pay_amount",       "transform": "cumulative_sum"},
                "first_order_date": {"source": "dwt(T-1).first_order_date", "transform": "carry_forward"},
                "last_order_date":  {"source": "biz_dt",               "transform": "literal"},
            },
        },
        "ads": {
            "table": "ads_trade_dashboard_1d",
            "downstream_of": ["dws_trade_user_1d", "dwt_trade_user_td"],
            "fields": {
                "metric_name":  {"source": "literal", "transform": "derived"},
                "metric_value": {"source": "dws.* + dwt.*", "transform": "aggregate + cumulative"},
            },
        },
    },
}

USER_LINEAGE: dict[str, Any] = {
    "domain": "user",
    "layers": {
        "dim": {
            "table": "dim_user_info",
            "downstream_of": ["ods_user_user_info_dic"],
            "fields": {
                "user_id":       {"source": "ods_user.id",            "transform": "rename"},
                "user_name":     {"source": "ods_user.user_name",     "transform": "direct"},
                "mobile":        {"source": "ods_user.mobile",        "transform": "direct (masked)"},
                "email":         {"source": "ods_user.email",         "transform": "direct (masked)"},
                "register_time": {"source": "ods_user.register_time", "transform": "direct"},
            },
        },
    },
}

ALL_LINEAGES = [COMMENT_LINEAGE, TRADE_LINEAGE, USER_LINEAGE]


# ---------------------------------------------------------------------------
# Lineage queries
# ---------------------------------------------------------------------------

class LineageGraph:
    """Query field-level lineage across warehouse layers."""

    def __init__(self, lineages: list[dict[str, Any]] | None = None) -> None:
        self.lineages = lineages or ALL_LINEAGES

    def upstream_of(self, layer: str, field: str, domain: str | None = None) -> list[str]:
        """Trace a field back to its source. Returns list of upstream origins."""
        results: list[str] = []
        for lin in self.lineages:
            if domain and lin["domain"] != domain:
                continue
            for lname, ldef in lin["layers"].items():
                if lname != layer:
                    continue
                field_info = ldef.get("fields", {}).get(field)
                if field_info:
                    results.append(field_info.get("source", "unknown"))
        return results

    def downstream_of(self, layer: str, field: str, domain: str | None = None) -> list[dict[str, str]]:
        """Find all downstream fields derived from this source field."""
        results: list[dict[str, str]] = []
        for lin in self.lineages:
            if domain and lin["domain"] != domain:
                continue
            for lname, ldef in lin["layers"].items():
                for fname, finfo in ldef.get("fields", {}).items():
                    source = finfo.get("source", "")
                    if layer in source and field in source:
                        results.append({"domain": lin["domain"], "layer": lname, "field": fname})
        return results

    def full_lineage(self, domain: str | None = None) -> dict[str, Any]:
        """Return the complete lineage graph."""
        filtered = [lin for lin in self.lineages if domain is None or lin["domain"] == domain]
        return {"domains": filtered}

    def export(self, path: str | Path, domain: str | None = None) -> Path:
        """Export lineage graph as JSON."""
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(self.full_lineage(domain), ensure_ascii=False, indent=2), encoding="utf-8")
        return p

    def validate(self) -> list[str]:
        """Check lineage graph for broken references. Returns list of warnings."""
        # Build global table registry across all domains
        all_tables: set[str] = set()
        for lin in self.lineages:
            for ldef in lin["layers"].values():
                table = ldef.get("table", "")
                if table:
                    all_tables.add(table)

        warnings: list[str] = []
        for lin in self.lineages:
            domain = lin["domain"]
            for lname, ldef in lin["layers"].items():
                upstream = ldef.get("downstream_of", [])
                for up in upstream:
                    up_table = up.split("(")[0]  # strip (T-1) suffix
                    # Also match self-references (e.g. dwt_trade_user_td referencing itself)
                    if up_table not in all_tables:
                        warnings.append(f"[{domain}] {lname} references unknown upstream: {up_table}")
        return warnings

    def impact_analysis(self, source_field: str) -> dict[str, Any]:
        """Given a source field name, find all downstream fields it impacts."""
        impacted: list[dict[str, str]] = []
        for lin in self.lineages:
            for lname, ldef in lin["layers"].items():
                for fname, finfo in ldef.get("fields", {}).items():
                    if source_field in str(finfo.get("source", "")):
                        impacted.append({
                            "domain": lin["domain"],
                            "layer": lname,
                            "table": ldef.get("table", "?"),
                            "field": fname,
                            "transform": finfo.get("transform", "?"),
                        })
        return {"source_field": source_field, "impacted_count": len(impacted), "impacted": impacted}
