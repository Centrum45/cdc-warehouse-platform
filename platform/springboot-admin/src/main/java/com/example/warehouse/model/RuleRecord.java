package com.example.warehouse.model;

public class RuleRecord {
    private Long id;
    private String ruleCategory;
    private String databaseName;
    private String tableName;
    private String columnName;
    private String ruleType;
    private String ruleValue;
    private String action;

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public String getRuleCategory() { return ruleCategory; }
    public void setRuleCategory(String ruleCategory) { this.ruleCategory = ruleCategory; }
    public String getDatabaseName() { return databaseName; }
    public void setDatabaseName(String databaseName) { this.databaseName = databaseName; }
    public String getTableName() { return tableName; }
    public void setTableName(String tableName) { this.tableName = tableName; }
    public String getColumnName() { return columnName; }
    public void setColumnName(String columnName) { this.columnName = columnName; }
    public String getRuleType() { return ruleType; }
    public void setRuleType(String ruleType) { this.ruleType = ruleType; }
    public String getRuleValue() { return ruleValue; }
    public void setRuleValue(String ruleValue) { this.ruleValue = ruleValue; }
    public String getAction() { return action; }
    public void setAction(String action) { this.action = action; }
}
