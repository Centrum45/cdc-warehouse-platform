package com.example.warehouse.repository;

import com.example.warehouse.model.MonitorResult;
import java.util.List;
import org.springframework.dao.DataAccessException;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Repository;

@Repository
public class MonitorResultRepository {
    private final JdbcTemplate jdbcTemplate;

    public MonitorResultRepository(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }

    public List<MonitorResult> findLatest() {
        try {
            return jdbcTemplate.query(
                    "select * from monitor_result order by id desc limit 50",
                    (rs, rowNum) -> {
                        MonitorResult result = new MonitorResult();
                        result.setId(rs.getLong("id"));
                        result.setMonitorType(rs.getString("monitor_type"));
                        result.setDatabaseName(rs.getString("source_database"));
                        result.setTableName(rs.getString("source_table"));
                        result.setStatus(rs.getString("status"));
                        result.setMessage(rs.getString("message"));
                        result.setMetricValue(rs.getString("metric_value"));
                        result.setCreatedAt(String.valueOf(rs.getTimestamp("created_at")));
                        return result;
                    }
            );
        } catch (DataAccessException ex) {
            return java.util.Collections.emptyList();
        }
    }
}
