package com.example.warehouse.model;

import java.util.ArrayList;
import java.util.List;

public class RealtimeSnapshot {
    private boolean impalaConnected;
    private String message;
    private String kuduMasterUrl;
    private String impalaUrl;
    private List<RealtimeTableView> tables = new ArrayList<>();
    private HiveQueryResult commentAnalysis = new HiveQueryResult();
    private HiveQueryResult tradeAnalysis = new HiveQueryResult();
    private HiveQueryResult userAnalysis = new HiveQueryResult();

    public boolean isImpalaConnected() { return impalaConnected; }
    public void setImpalaConnected(boolean impalaConnected) { this.impalaConnected = impalaConnected; }
    public String getMessage() { return message; }
    public void setMessage(String message) { this.message = message; }
    public String getKuduMasterUrl() { return kuduMasterUrl; }
    public void setKuduMasterUrl(String kuduMasterUrl) { this.kuduMasterUrl = kuduMasterUrl; }
    public String getImpalaUrl() { return impalaUrl; }
    public void setImpalaUrl(String impalaUrl) { this.impalaUrl = impalaUrl; }
    public List<RealtimeTableView> getTables() { return tables; }
    public void setTables(List<RealtimeTableView> tables) { this.tables = tables; }
    public HiveQueryResult getCommentAnalysis() { return commentAnalysis; }
    public void setCommentAnalysis(HiveQueryResult commentAnalysis) { this.commentAnalysis = commentAnalysis; }
    public HiveQueryResult getTradeAnalysis() { return tradeAnalysis; }
    public void setTradeAnalysis(HiveQueryResult tradeAnalysis) { this.tradeAnalysis = tradeAnalysis; }
    public HiveQueryResult getUserAnalysis() { return userAnalysis; }
    public void setUserAnalysis(HiveQueryResult userAnalysis) { this.userAnalysis = userAnalysis; }
}
