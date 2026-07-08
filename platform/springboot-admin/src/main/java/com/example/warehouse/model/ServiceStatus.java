package com.example.warehouse.model;

public class ServiceStatus {
    private String name;
    private String status;
    private String ports;
    private boolean running;

    public String getName() { return name; }
    public void setName(String name) { this.name = name; }
    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }
    public String getPorts() { return ports; }
    public void setPorts(String ports) { this.ports = ports; }
    public boolean isRunning() { return running; }
    public void setRunning(boolean running) { this.running = running; }
}
