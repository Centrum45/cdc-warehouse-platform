package com.example.warehouse.model;

public class HiveQueryRequest {
    private String sql;
    private Integer limit;

    public String getSql() { return sql; }
    public void setSql(String sql) { this.sql = sql; }
    public Integer getLimit() { return limit; }
    public void setLimit(Integer limit) { this.limit = limit; }
}
