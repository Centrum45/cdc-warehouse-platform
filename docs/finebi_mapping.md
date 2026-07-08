# FineBI Mapping

ADS table:

```text
ads.ads_comment_dashboard_1d
```

Dataset fields:

| Field | Meaning |
| --- | --- |
| metric_name | Metric code |
| metric_value | Metric value |
| dt | Business date partition |

Recommended FineBI charts:

| Chart | Filter | Metric |
| --- | --- | --- |
| Comment batch total | dt | comment_batch_total |
| Priority batch total | dt | comment_batch_priority_total |

Refresh strategy:

```text
DolphinScheduler ADS task success
  -> FineBI dataset refresh
  -> dashboard cache refresh
```
