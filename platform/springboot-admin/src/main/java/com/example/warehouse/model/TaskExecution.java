package com.example.warehouse.model;

public class TaskExecution {
    private Long id;
    private String taskName;
    private String taskType;
    private String command;
    private String status;
    private Integer exitCode;
    private String outputExcerpt;
    private Long durationMs;
    private String createdAt;

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public String getTaskName() { return taskName; }
    public void setTaskName(String taskName) { this.taskName = taskName; }
    public String getTaskType() { return taskType; }
    public void setTaskType(String taskType) { this.taskType = taskType; }
    public String getCommand() { return command; }
    public void setCommand(String command) { this.command = command; }
    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }
    public Integer getExitCode() { return exitCode; }
    public void setExitCode(Integer exitCode) { this.exitCode = exitCode; }
    public String getOutputExcerpt() { return outputExcerpt; }
    public void setOutputExcerpt(String outputExcerpt) { this.outputExcerpt = outputExcerpt; }
    public Long getDurationMs() { return durationMs; }
    public void setDurationMs(Long durationMs) { this.durationMs = durationMs; }
    public String getCreatedAt() { return createdAt; }
    public void setCreatedAt(String createdAt) { this.createdAt = createdAt; }
}
