package com.example.warehouse.repository;

import com.example.warehouse.model.ReplayRequest;
import org.springframework.dao.DataAccessException;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Repository;

@Repository
public class ReplayRepository {
    private final JdbcTemplate jdbcTemplate;

    public ReplayRepository(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }

    public void save(ReplayRequest request, String command) {
        try {
            jdbcTemplate.update(
                    "insert into replay_record (source_database, source_table, start_time, end_time, command, status) values (?, ?, ?, ?, ?, ?)",
                    request.getDatabaseName(),
                    request.getTableName(),
                    request.getStartTime(),
                    request.getEndTime(),
                    command,
                    "CREATED"
            );
        } catch (DataAccessException ignored) {
        }
    }
}
