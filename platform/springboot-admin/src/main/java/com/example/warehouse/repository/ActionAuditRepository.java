package com.example.warehouse.repository;

import com.example.warehouse.model.ActionAudit;
import java.util.Collections;
import java.util.List;
import javax.annotation.PostConstruct;
import org.springframework.dao.DataAccessException;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Repository;

@Repository
public class ActionAuditRepository {
    private final JdbcTemplate jdbcTemplate;

    public ActionAuditRepository(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }

    @PostConstruct
    public void ensureTable() {
        try {
            jdbcTemplate.execute(
                    "create table if not exists action_audit ("
                            + "id bigint primary key auto_increment,"
                            + "action_name varchar(128) not null,"
                            + "operator varchar(128) not null,"
                            + "client_ip varchar(64),"
                            + "request_json text,"
                            + "exit_code int,"
                            + "output_excerpt text,"
                            + "duration_ms bigint,"
                            + "created_at timestamp not null default current_timestamp,"
                            + "key idx_action_created_at (created_at),"
                            + "key idx_action_name (action_name)"
                            + ")"
            );
        } catch (DataAccessException ignored) {
            // Existing deployments may start before MySQL is fully ready.
        }
    }

    public void save(String actionName, String operator, String clientIp, String requestJson,
                     int exitCode, String output, long durationMs) {
        String excerpt = output == null ? "" : output;
        if (excerpt.length() > 4000) {
            excerpt = excerpt.substring(0, 4000);
        }
        try {
            jdbcTemplate.update(
                    "insert into action_audit(action_name, operator, client_ip, request_json, exit_code, output_excerpt, duration_ms) values(?,?,?,?,?,?,?)",
                    actionName, operator, clientIp, requestJson, exitCode, excerpt, durationMs
            );
        } catch (DataAccessException ignored) {
            // Audit failure must not block the operation itself.
        }
    }

    public List<ActionAudit> findLatest(int limit) {
        try {
            return jdbcTemplate.query(
                    "select * from action_audit order by id desc limit ?",
                    (rs, rowNum) -> {
                        ActionAudit audit = new ActionAudit();
                        audit.setId(rs.getLong("id"));
                        audit.setActionName(rs.getString("action_name"));
                        audit.setOperator(rs.getString("operator"));
                        audit.setClientIp(rs.getString("client_ip"));
                        audit.setRequestJson(rs.getString("request_json"));
                        audit.setExitCode(rs.getInt("exit_code"));
                        audit.setOutputExcerpt(rs.getString("output_excerpt"));
                        audit.setDurationMs(rs.getLong("duration_ms"));
                        audit.setCreatedAt(String.valueOf(rs.getTimestamp("created_at")));
                        return audit;
                    },
                    limit
            );
        } catch (DataAccessException ex) {
            return Collections.emptyList();
        }
    }
}
