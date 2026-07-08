package com.example.warehouse.model;

import java.util.List;

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
    public List<String> getPrimaryKeys() { return primaryKeys; }
    public void setPrimaryKeys(List<String> primaryKeys) { this.primaryKeys = primaryKeys; }
    public String getVersionColumn() { return versionColumn; }
    public void setVersionColumn(String versionColumn) { this.versionColumn = versionColumn; }
    public String getPartitionColumn() { return partitionColumn; }
    public void setPartitionColumn(String partitionColumn) { this.partitionColumn = partitionColumn; }
    public String getColumnsJson() { return columnsJson; }
    public void setColumnsJson(String columnsJson) { this.columnsJson = columnsJson; }
}
