package com.example.warehouse.model;

import java.util.ArrayList;
import java.util.List;

public class DashboardSnapshot {
    private String containerStatus;
    private String kafkaTopics;
    private String maxwellLogs;
    private String kafkaLogs;
    private String sparkStreamingLogs;
    private String sparkSqlMergeLogs;
    private String adminLogs;
    private String hdfsWarehouseListing;
    private String hdfsNamenodeLogs;
    private String hiveDatabases;
    private String hiveServerLogs;
    private String refreshedAt;
    private List<TableStorageView> tableStorage = new ArrayList<>();
    private List<ServiceStatus> serviceStatuses = new ArrayList<>();
    private List<WarehouseLayerView> warehouseLayers = new ArrayList<>();

    public String getContainerStatus() { return containerStatus; }
    public void setContainerStatus(String containerStatus) { this.containerStatus = containerStatus; }
    public String getKafkaTopics() { return kafkaTopics; }
    public void setKafkaTopics(String kafkaTopics) { this.kafkaTopics = kafkaTopics; }
    public String getMaxwellLogs() { return maxwellLogs; }
    public void setMaxwellLogs(String maxwellLogs) { this.maxwellLogs = maxwellLogs; }
    public String getKafkaLogs() { return kafkaLogs; }
    public void setKafkaLogs(String kafkaLogs) { this.kafkaLogs = kafkaLogs; }
    public String getSparkStreamingLogs() { return sparkStreamingLogs; }
    public void setSparkStreamingLogs(String sparkStreamingLogs) { this.sparkStreamingLogs = sparkStreamingLogs; }
    public String getSparkSqlMergeLogs() { return sparkSqlMergeLogs; }
    public void setSparkSqlMergeLogs(String sparkSqlMergeLogs) { this.sparkSqlMergeLogs = sparkSqlMergeLogs; }
    public String getAdminLogs() { return adminLogs; }
    public void setAdminLogs(String adminLogs) { this.adminLogs = adminLogs; }
    public String getHdfsWarehouseListing() { return hdfsWarehouseListing; }
    public void setHdfsWarehouseListing(String hdfsWarehouseListing) { this.hdfsWarehouseListing = hdfsWarehouseListing; }
    public String getHdfsNamenodeLogs() { return hdfsNamenodeLogs; }
    public void setHdfsNamenodeLogs(String hdfsNamenodeLogs) { this.hdfsNamenodeLogs = hdfsNamenodeLogs; }
    public String getHiveDatabases() { return hiveDatabases; }
    public void setHiveDatabases(String hiveDatabases) { this.hiveDatabases = hiveDatabases; }
    public String getHiveServerLogs() { return hiveServerLogs; }
    public void setHiveServerLogs(String hiveServerLogs) { this.hiveServerLogs = hiveServerLogs; }
    public String getRefreshedAt() { return refreshedAt; }
    public void setRefreshedAt(String refreshedAt) { this.refreshedAt = refreshedAt; }
    public List<TableStorageView> getTableStorage() { return tableStorage; }
    public void setTableStorage(List<TableStorageView> tableStorage) { this.tableStorage = tableStorage; }
    public List<ServiceStatus> getServiceStatuses() { return serviceStatuses; }
    public void setServiceStatuses(List<ServiceStatus> serviceStatuses) { this.serviceStatuses = serviceStatuses; }
    public List<WarehouseLayerView> getWarehouseLayers() { return warehouseLayers; }
    public void setWarehouseLayers(List<WarehouseLayerView> warehouseLayers) { this.warehouseLayers = warehouseLayers; }
}
