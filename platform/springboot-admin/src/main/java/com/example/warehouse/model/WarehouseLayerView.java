package com.example.warehouse.model;

import java.util.ArrayList;
import java.util.List;

public class WarehouseLayerView {
    private String layer;
    private int tableCount;
    private int partitionCount;
    private List<WarehouseTableView> tables = new ArrayList<>();

    public String getLayer() { return layer; }
    public void setLayer(String layer) { this.layer = layer; }
    public int getTableCount() { return tableCount; }
    public void setTableCount(int tableCount) { this.tableCount = tableCount; }
    public int getPartitionCount() { return partitionCount; }
    public void setPartitionCount(int partitionCount) { this.partitionCount = partitionCount; }
    public List<WarehouseTableView> getTables() { return tables; }
    public void setTables(List<WarehouseTableView> tables) { this.tables = tables; }
}
