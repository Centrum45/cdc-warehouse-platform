package com.example.warehouse.model;

public class TableOpsRequest {
    private String databaseName;
    private String tableName;
    private String bizDt;
    private String startDt;
    private String endDt;
    private Boolean dryRun;

    public String getDatabaseName() { return databaseName; }
    public void setDatabaseName(String databaseName) { this.databaseName = databaseName; }
    public String getTableName() { return tableName; }
    public void setTableName(String tableName) { this.tableName = tableName; }
    public String getBizDt() { return bizDt; }
    public void setBizDt(String bizDt) { this.bizDt = bizDt; }
    public String getStartDt() { return startDt; }
    public void setStartDt(String startDt) { this.startDt = startDt; }
    public String getEndDt() { return endDt; }
    public void setEndDt(String endDt) { this.endDt = endDt; }
    public Boolean getDryRun() { return dryRun; }
    public void setDryRun(Boolean dryRun) { this.dryRun = dryRun; }
}
