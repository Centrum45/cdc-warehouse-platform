package com.example.warehouse.model;

public class RealtimeTableView {
    private String name;
    private long rowCount;
    private String latestUpdateTime;

    public String getName() { return name; }
    public void setName(String name) { this.name = name; }
    public long getRowCount() { return rowCount; }
    public void setRowCount(long rowCount) { this.rowCount = rowCount; }
    public String getLatestUpdateTime() { return latestUpdateTime; }
    public void setLatestUpdateTime(String latestUpdateTime) { this.latestUpdateTime = latestUpdateTime; }
}
