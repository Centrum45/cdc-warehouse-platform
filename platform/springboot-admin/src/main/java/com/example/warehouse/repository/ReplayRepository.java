package com.example.warehouse.repository;

import com.example.warehouse.model.ReplayRequest;
import com.example.warehouse.model.ReplayRecord;
import java.sql.PreparedStatement;
import java.sql.Statement;
import java.util.Collections;
import java.util.List;
import org.springframework.dao.DataAccessException;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.support.GeneratedKeyHolder;
import org.springframework.jdbc.support.KeyHolder;
import org.springframework.stereotype.Repository;

@Repository
public class ReplayRepository {
    private final JdbcTemplate jdbcTemplate;

    public ReplayRepository(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }

    public long save(ReplayRequest request, String command) {
        KeyHolder keyHolder = new GeneratedKeyHolder();
        jdbcTemplate.update(connection -> {
            PreparedStatement statement = connection.prepareStatement(
                    "insert into replay_record (source_database, source_table, start_time, end_time, command, status) values (?, ?, ?, ?, ?, ?)",
                    Statement.RETURN_GENERATED_KEYS
            );
            statement.setString(1, request.getDatabaseName());
            statement.setString(2, request.getTableName());
            statement.setString(3, empty(request.getStartTime()));
            statement.setString(4, empty(request.getEndTime()));
            statement.setString(5, command);
            statement.setString(6, "RUNNING");
            return statement;
        }, keyHolder);
        return keyHolder.getKey() == null ? 0L : keyHolder.getKey().longValue();
    }

    public void updateStatus(long id, String status) {
        if (id <= 0L) {
            return;
        }
        try {
            jdbcTemplate.update("update replay_record set status = ? where id = ?", status, id);
        } catch (DataAccessException ignored) {
        }
    }

    public List<ReplayRecord> findLatest(int limit) {
        try {
            return jdbcTemplate.query(
                    "select id, source_database, source_table, start_time, end_time, command, status, created_at, updated_at "
                            + "from replay_record order by id desc limit ?",
                    (rs, rowNum) -> {
                        ReplayRecord record = new ReplayRecord();
                        record.setId(rs.getLong("id"));
                        record.setDatabaseName(rs.getString("source_database"));
                        record.setTableName(rs.getString("source_table"));
                        record.setStartTime(rs.getString("start_time"));
                        record.setEndTime(rs.getString("end_time"));
                        record.setCommand(rs.getString("command"));
                        record.setStatus(rs.getString("status"));
                        record.setCreatedAt(String.valueOf(rs.getTimestamp("created_at")));
                        record.setUpdatedAt(String.valueOf(rs.getTimestamp("updated_at")));
                        return record;
                    },
                    limit
            );
        } catch (DataAccessException ignored) {
            return Collections.emptyList();
        }
    }

    private String empty(String value) {
        return value == null ? "" : value.trim();
    }
}
