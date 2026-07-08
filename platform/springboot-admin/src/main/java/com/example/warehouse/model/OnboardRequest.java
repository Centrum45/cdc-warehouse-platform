package com.example.warehouse.model;

public class OnboardRequest {
    private String databaseName;
    private String tableName;
    private String dbaMetadataPath;
    private String primaryKeys;
    private String versionColumn;
    private String partitionColumn;

    public String getDatabaseName() { return databaseName; }
    public void setDatabaseName(String databaseName) { this.databaseName = databaseName; }
    public String getTableName() { return tableName; }
    public void setTableName(String tableName) { this.tableName = tableName; }
    public String getDbaMetadataPath() { return dbaMetadataPath; }
    public void setDbaMetadataPath(String dbaMetadataPath) { this.dbaMetadataPath = dbaMetadataPath; }
    public String getPrimaryKeys() { return primaryKeys; }
    public void setPrimaryKeys(String primaryKeys) { this.primaryKeys = primaryKeys; }
    public String getVersionColumn() { return versionColumn; }
    public void setVersionColumn(String versionColumn) { this.versionColumn = versionColumn; }
    public String getPartitionColumn() { return partitionColumn; }
    public void setPartitionColumn(String partitionColumn) { this.partitionColumn = partitionColumn; }
}
