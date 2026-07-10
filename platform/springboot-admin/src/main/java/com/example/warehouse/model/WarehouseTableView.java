package com.example.warehouse.model;

import java.util.ArrayList;
import java.util.List;

public class WarehouseTableView {
    private String layer;
    private String table;
    private List<String> partitions = new ArrayList<>();
    private String latestPartition;
    private String latestPath;
    private String samplePath;
    private String sample;
    private long rowCount;
    private boolean hdfs;

    public String getLayer() { return layer; }
    public void setLayer(String layer) { this.layer = layer; }
    public String getTable() { return table; }
    public void setTable(String table) { this.table = table; }
    public List<String> getPartitions() { return partitions; }
    public void setPartitions(List<String> partitions) { this.partitions = partitions; }
    public String getLatestPartition() { return latestPartition; }
    public void setLatestPartition(String latestPartition) { this.latestPartition = latestPartition; }
    public String getLatestPath() { return latestPath; }
    public void setLatestPath(String latestPath) { this.latestPath = latestPath; }
    public String getSamplePath() { return samplePath; }
    public void setSamplePath(String samplePath) { this.samplePath = samplePath; }
    public String getSample() { return sample; }
    public void setSample(String sample) { this.sample = sample; }
    public long getRowCount() { return rowCount; }
    public void setRowCount(long rowCount) { this.rowCount = rowCount; }
    public boolean isHdfs() { return hdfs; }
    public void setHdfs(boolean hdfs) { this.hdfs = hdfs; }
}
