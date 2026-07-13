package com.example.warehouse.service;

import com.example.warehouse.model.HiveQueryResult;
import com.example.warehouse.model.RealtimeSnapshot;
import com.example.warehouse.model.RealtimeTableView;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.ResultSet;
import java.sql.Statement;
import java.util.Arrays;
import java.util.List;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

@Service
public class RealtimeService {
    private final String jdbcUrl;
    private final String username;
    private final String password;
    private final String kuduMasterUrl;
    private final String impalaUrl;
    private final HiveQueryService hiveQueryService;

    public RealtimeService(
            @Value("${warehouse.impala.jdbc-url:${IMPALA_JDBC_URL:jdbc:hive2://localhost:21050/realtime;transportMode=binary;auth=noSasl}}") String jdbcUrl,
            @Value("${warehouse.impala.username:${IMPALA_USER:}}") String username,
            @Value("${warehouse.impala.password:${IMPALA_PASSWORD:}}") String password,
            @Value("${warehouse.impala.kudu-master-url:${KUDU_MASTER_URL:http://localhost:8051}}") String kuduMasterUrl,
            @Value("${warehouse.impala.ui-url:${IMPALA_UI_URL:http://localhost:25000}}") String impalaUrl,
            HiveQueryService hiveQueryService) {
        this.jdbcUrl = jdbcUrl;
        this.username = username;
        this.password = password;
        this.kuduMasterUrl = kuduMasterUrl;
        this.impalaUrl = impalaUrl;
        this.hiveQueryService = hiveQueryService;
    }

    public RealtimeSnapshot snapshot() {
        RealtimeSnapshot snapshot = new RealtimeSnapshot();
        snapshot.setKuduMasterUrl(kuduMasterUrl);
        snapshot.setImpalaUrl(impalaUrl);
        try {
            Class.forName("org.apache.hive.jdbc.HiveDriver");
            try (Connection connection = DriverManager.getConnection(jdbcUrl, username, password)) {
                snapshot.setImpalaConnected(true);
                snapshot.setMessage("OK");
                snapshot.setTables(loadTables(connection));
            }
        } catch (Exception ex) {
            snapshot.setImpalaConnected(false);
            snapshot.setMessage(ex.getMessage());
        }
        snapshot.setCommentAnalysis(query("select * from realtime.v_realtime_comment_analysis limit 50"));
        snapshot.setTradeAnalysis(query("select * from realtime.v_realtime_trade_analysis limit 50"));
        snapshot.setUserAnalysis(query("select * from realtime.v_realtime_user_analysis limit 50"));
        return snapshot;
    }

    private List<RealtimeTableView> loadTables(Connection connection) {
        List<RealtimeTableView> tables = Arrays.asList(table("avatar_commentbatchsource"), table("order_info"), table("user_info"));
        for (RealtimeTableView table : tables) {
            try (Statement statement = connection.createStatement();
                 ResultSet rs = statement.executeQuery("select count(1), max(" + latestColumn(table.getName()) + ") from realtime." + table.getName())) {
                if (rs.next()) {
                    table.setRowCount(rs.getLong(1));
                    table.setLatestUpdateTime(rs.getString(2));
                }
            } catch (Exception ex) {
                table.setLatestUpdateTime(ex.getMessage());
            }
        }
        return tables;
    }

    private RealtimeTableView table(String name) {
        RealtimeTableView table = new RealtimeTableView();
        table.setName(name);
        return table;
    }

    private String latestColumn(String table) {
        if ("user_info".equals(table)) {
            return "utime";
        }
        return "utime";
    }

    private HiveQueryResult query(String sql) {
        return hiveQueryService.queryWithJdbc(sql, 50, jdbcUrl, username, password);
    }
}
