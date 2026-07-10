package com.example.warehouse.model;

import java.util.List;
import java.util.Arrays;
import java.util.stream.Collectors;

public class TableMetadata {
    private Long id;
    private String databaseName;
    private String tableName;
    private String odsBinlogTable;
    private String odsTable;
    private List<String> primaryKeys;
    private String versionColumn;
    private String partitionColumn;
    private String columnsJson;

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public String getDatabaseName() { return databaseName; }
    public void setDatabaseName(String databaseName) { this.databaseName = databaseName; }
    public String getTableName() { return tableName; }
    public void setTableName(String tableName) { this.tableName = tableName; }
    public String getOdsBinlogTable() { return odsBinlogTable; }
    public void setOdsBinlogTable(String odsBinlogTable) { this.odsBinlogTable = odsBinlogTable; }
    public String getOdsTable() { return odsTable; }
    public void setOdsTable(String odsTable) { this.odsTable = odsTable; }
    public void setHiveTable(String hiveTable) { this.odsTable = hiveTable; }
    public List<String> getPrimaryKeys() { return primaryKeys; }
    public void setPrimaryKeys(List<String> primaryKeys) { this.primaryKeys = primaryKeys; }
    public void setPrimaryKeys(String primaryKeys) {
        this.primaryKeys = Arrays.stream(primaryKeys.split(","))
                .map(String::trim)
                .filter(item -> !item.isEmpty())
                .collect(Collectors.toList());
    }
    public String getVersionColumn() { return versionColumn; }
    public void setVersionColumn(String versionColumn) { this.versionColumn = versionColumn; }
    public String getPartitionColumn() { return partitionColumn; }
    public void setPartitionColumn(String partitionColumn) { this.partitionColumn = partitionColumn; }
    public void setPartitionFormat(String partitionFormat) { this.partitionColumn = partitionFormat; }
    public String getColumnsJson() { return columnsJson; }
    public void setColumnsJson(String columnsJson) { this.columnsJson = columnsJson; }
}
