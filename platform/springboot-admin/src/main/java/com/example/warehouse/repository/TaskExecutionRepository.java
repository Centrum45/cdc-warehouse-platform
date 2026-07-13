package com.example.warehouse.repository;

import com.example.warehouse.model.TaskExecution;
import java.util.Collections;
import java.util.List;
import java.util.Optional;
import javax.annotation.PostConstruct;
import org.springframework.dao.DataAccessException;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Repository;

@Repository
public class TaskExecutionRepository {
    private final JdbcTemplate jdbcTemplate;

    public TaskExecutionRepository(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }

    @PostConstruct
    public void ensureTable() {
        try {
            jdbcTemplate.execute(
                    "create table if not exists task_execution ("
                            + "id bigint primary key auto_increment,"
                            + "task_name varchar(256) not null,"
                            + "task_type varchar(64) not null,"
                            + "command text not null,"
                            + "status varchar(32) not null,"
                            + "exit_code int,"
                            + "output_excerpt text,"
                            + "duration_ms bigint,"
                            + "created_at timestamp not null default current_timestamp,"
                            + "key idx_task_execution_created_at (created_at),"
                            + "key idx_task_execution_name (task_name)"
                            + ")"
            );
        } catch (DataAccessException ignored) {
        }
    }

    public void save(String taskName, String taskType, String command, int exitCode, String output, long durationMs) {
        String excerpt = output == null ? "" : output;
        if (excerpt.length() > 4000) {
            excerpt = excerpt.substring(0, 4000);
        }
        String status = exitCode == 0 ? "SUCCESS" : "FAILED";
        try {
            jdbcTemplate.update(
                    "insert into task_execution(task_name, task_type, command, status, exit_code, output_excerpt, duration_ms) values(?,?,?,?,?,?,?)",
                    taskName, taskType, command, status, exitCode, excerpt, durationMs
            );
        } catch (DataAccessException ignored) {
        }
    }

    public List<TaskExecution> findLatest(int limit) {
        try {
            return jdbcTemplate.query(
                    "select * from task_execution order by id desc limit ?",
                    (rs, rowNum) -> {
                        TaskExecution item = new TaskExecution();
                        item.setId(rs.getLong("id"));
                        item.setTaskName(rs.getString("task_name"));
                        item.setTaskType(rs.getString("task_type"));
                        item.setCommand(rs.getString("command"));
                        item.setStatus(rs.getString("status"));
                        item.setExitCode(rs.getInt("exit_code"));
                        item.setOutputExcerpt(rs.getString("output_excerpt"));
                        item.setDurationMs(rs.getLong("duration_ms"));
                        item.setCreatedAt(String.valueOf(rs.getTimestamp("created_at")));
                        return item;
                    },
                    limit
            );
        } catch (DataAccessException ex) {
            return Collections.emptyList();
        }
    }

    public Optional<TaskExecution> findById(long id) {
        try {
            List<TaskExecution> items = jdbcTemplate.query(
                    "select * from task_execution where id = ?",
                    (rs, rowNum) -> map(rs),
                    id
            );
            return items.isEmpty() ? Optional.empty() : Optional.of(items.get(0));
        } catch (DataAccessException ex) {
            return Optional.empty();
        }
    }

    private TaskExecution map(java.sql.ResultSet rs) throws java.sql.SQLException {
        TaskExecution item = new TaskExecution();
        item.setId(rs.getLong("id"));
        item.setTaskName(rs.getString("task_name"));
        item.setTaskType(rs.getString("task_type"));
        item.setCommand(rs.getString("command"));
        item.setStatus(rs.getString("status"));
        item.setExitCode(rs.getInt("exit_code"));
        item.setOutputExcerpt(rs.getString("output_excerpt"));
        item.setDurationMs(rs.getLong("duration_ms"));
        item.setCreatedAt(String.valueOf(rs.getTimestamp("created_at")));
        return item;
    }
}
