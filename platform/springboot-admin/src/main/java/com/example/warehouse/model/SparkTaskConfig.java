package com.example.warehouse.model;

public class SparkTaskConfig {
    private String taskName;
    private String taskType;
    private String command;
    private String schedule;

    public String getTaskName() { return taskName; }
    public void setTaskName(String taskName) { this.taskName = taskName; }
    public String getTaskType() { return taskType; }
    public void setTaskType(String taskType) { this.taskType = taskType; }
    public String getCommand() { return command; }
    public void setCommand(String command) { this.command = command; }
    public String getSchedule() { return schedule; }
    public void setSchedule(String schedule) { this.schedule = schedule; }
}
