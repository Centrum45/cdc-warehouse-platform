package com.example.warehouse.model;

import java.util.ArrayList;
import java.util.List;

public class HiveQueryResult {
    private int exitCode;
    private String message;
    private List<String> columns = new ArrayList<>();
    private List<List<String>> rows = new ArrayList<>();

    public int getExitCode() { return exitCode; }
    public void setExitCode(int exitCode) { this.exitCode = exitCode; }
    public String getMessage() { return message; }
    public void setMessage(String message) { this.message = message; }
    public List<String> getColumns() { return columns; }
    public void setColumns(List<String> columns) { this.columns = columns; }
    public List<List<String>> getRows() { return rows; }
    public void setRows(List<List<String>> rows) { this.rows = rows; }
}
