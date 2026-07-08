package com.example.warehouse.model;

public class TableStorageView {
    private String databaseName;
    private String tableName;
    private String odsBinlogPath;
    private String odsPath;
    private String odsBinlogSample;
    private String odsSample;

    public String getDatabaseName() { return databaseName; }
    public void setDatabaseName(String databaseName) { this.databaseName = databaseName; }
    public String getTableName() { return tableName; }
    public void setTableName(String tableName) { this.tableName = tableName; }
    public String getOdsBinlogPath() { return odsBinlogPath; }
    public void setOdsBinlogPath(String odsBinlogPath) { this.odsBinlogPath = odsBinlogPath; }
    public String getOdsPath() { return odsPath; }
    public void setOdsPath(String odsPath) { this.odsPath = odsPath; }
    public String getOdsBinlogSample() { return odsBinlogSample; }
    public void setOdsBinlogSample(String odsBinlogSample) { this.odsBinlogSample = odsBinlogSample; }
    public String getOdsSample() { return odsSample; }
    public void setOdsSample(String odsSample) { this.odsSample = odsSample; }
}
