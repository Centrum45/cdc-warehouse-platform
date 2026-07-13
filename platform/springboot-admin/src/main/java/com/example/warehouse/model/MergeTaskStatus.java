package com.example.warehouse.model;

public class MergeTaskStatus {
    private Long id;
    private String sourceDatabase;
    private String sourceTable;
    private String processDt;
    private String runId;
    private String status;
    private Integer binlogRows;
    private Integer oldRows;
    private Integer outputRows;
    private String targetPartitions;
    private String auditPath;
    private String updatedAt;

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public String getSourceDatabase() { return sourceDatabase; }
    public void setSourceDatabase(String sourceDatabase) { this.sourceDatabase = sourceDatabase; }
    public String getSourceTable() { return sourceTable; }
    public void setSourceTable(String sourceTable) { this.sourceTable = sourceTable; }
    public String getProcessDt() { return processDt; }
    public void setProcessDt(String processDt) { this.processDt = processDt; }
    public String getRunId() { return runId; }
    public void setRunId(String runId) { this.runId = runId; }
    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }
    public Integer getBinlogRows() { return binlogRows; }
    public void setBinlogRows(Integer binlogRows) { this.binlogRows = binlogRows; }
    public Integer getOldRows() { return oldRows; }
    public void setOldRows(Integer oldRows) { this.oldRows = oldRows; }
    public Integer getOutputRows() { return outputRows; }
    public void setOutputRows(Integer outputRows) { this.outputRows = outputRows; }
    public String getTargetPartitions() { return targetPartitions; }
    public void setTargetPartitions(String targetPartitions) { this.targetPartitions = targetPartitions; }
    public String getAuditPath() { return auditPath; }
    public void setAuditPath(String auditPath) { this.auditPath = auditPath; }
    public String getUpdatedAt() { return updatedAt; }
    public void setUpdatedAt(String updatedAt) { this.updatedAt = updatedAt; }
}
