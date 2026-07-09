package com.example.warehouse.service;

import com.example.warehouse.model.HiveQueryRequest;
import com.example.warehouse.model.HiveQueryResult;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.ResultSet;
import java.sql.ResultSetMetaData;
import java.sql.Statement;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

@Service
public class HiveQueryService {
    private final String jdbcUrl;
    private final String username;
    private final String password;

    public HiveQueryService(
            @Value("${warehouse.hive.jdbc-url:${HIVE_JDBC_URL:jdbc:hive2://localhost:10000/default}}") String jdbcUrl,
            @Value("${warehouse.hive.username:${HIVE_USER:root}}") String username,
            @Value("${warehouse.hive.password:${HIVE_PASSWORD:}}") String password) {
        this.jdbcUrl = jdbcUrl;
        this.username = username;
        this.password = password;
    }

    public HiveQueryResult query(HiveQueryRequest request) {
        HiveQueryResult result = new HiveQueryResult();
        String sql = request == null ? "" : safeTrim(request.getSql());
        int limit = request == null || request.getLimit() == null ? 100 : Math.max(1, Math.min(request.getLimit(), 500));
        if (sql.isEmpty()) {
            result.setExitCode(2);
            result.setMessage("sql is required");
            return result;
        }
        if (!isAllowed(sql)) {
            result.setExitCode(2);
            result.setMessage("only select/show/desc/describe/msck/use/explain statements are allowed");
            return result;
        }
        try {
            Class.forName("org.apache.hive.jdbc.HiveDriver");
            try (Connection connection = DriverManager.getConnection(jdbcUrl, username, password);
                 Statement statement = connection.createStatement()) {
                statement.setMaxRows(limit);
                boolean hasRows = statement.execute(sql);
                if (!hasRows) {
                    result.setExitCode(0);
                    result.setMessage("OK");
                    return result;
                }
                try (ResultSet rs = statement.getResultSet()) {
                    ResultSetMetaData meta = rs.getMetaData();
                    List<String> columns = new ArrayList<>();
                    for (int i = 1; i <= meta.getColumnCount(); i++) {
                        columns.add(meta.getColumnLabel(i));
                    }
                    result.setColumns(columns);
                    while (rs.next()) {
                        List<String> row = new ArrayList<>();
                        for (int i = 1; i <= meta.getColumnCount(); i++) {
                            Object value = rs.getObject(i);
                            row.add(value == null ? "" : String.valueOf(value));
                        }
                        result.getRows().add(row);
                    }
                }
                result.setExitCode(0);
                result.setMessage("OK rows=" + result.getRows().size());
            }
        } catch (Exception ex) {
            result.setExitCode(1);
            result.setMessage(ex.getMessage());
        }
        return result;
    }

    private boolean isAllowed(String sql) {
        String normalized = sql.trim().toLowerCase(Locale.ROOT);
        while (normalized.startsWith("(")) {
            normalized = normalized.substring(1).trim();
        }
        return normalized.startsWith("select ")
                || normalized.startsWith("show ")
                || normalized.startsWith("desc ")
                || normalized.startsWith("describe ")
                || normalized.startsWith("msck ")
                || normalized.startsWith("use ")
                || normalized.startsWith("explain ");
    }

    private String safeTrim(String value) {
        if (value == null) {
            return "";
        }
        String trimmed = value.trim();
        while (trimmed.endsWith(";")) {
            trimmed = trimmed.substring(0, trimmed.length() - 1).trim();
        }
        return trimmed;
    }
}
