package com.example.warehouse.repository;

import com.example.warehouse.model.MergeTaskStatus;
import java.util.Collections;
import java.util.List;
import javax.annotation.PostConstruct;
import org.springframework.dao.DataAccessException;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Repository;

@Repository
public class MergeTaskStatusRepository {
    private final JdbcTemplate jdbcTemplate;

    public MergeTaskStatusRepository(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }

    @PostConstruct
    public void ensureTable() {
        try {
            jdbcTemplate.execute(
                    "create table if not exists merge_task_status ("
                            + "id bigint primary key auto_increment,"
                            + "source_database varchar(128) not null,"
                            + "source_table varchar(128) not null,"
                            + "process_dt varchar(32) not null,"
                            + "run_id varchar(64) not null,"
                            + "status varchar(32) not null,"
                            + "binlog_rows int default 0,"
                            + "old_rows int default 0,"
                            + "output_rows int default 0,"
                            + "target_partitions text,"
                            + "audit_path varchar(1024),"
                            + "updated_at timestamp not null default current_timestamp on update current_timestamp,"
                            + "unique key uk_merge_run (source_database, source_table, process_dt, run_id),"
                            + "key idx_merge_updated_at (updated_at),"
                            + "key idx_merge_table_dt (source_database, source_table, process_dt)"
                            + ")"
            );
        } catch (DataAccessException ignored) {
        }
    }

    public void upsert(MergeTaskStatus status) {
        try {
            jdbcTemplate.update(
                    "insert into merge_task_status(source_database, source_table, process_dt, run_id, status, binlog_rows, old_rows, output_rows, target_partitions, audit_path) "
                            + "values(?,?,?,?,?,?,?,?,?,?) "
                            + "on duplicate key update status=values(status), binlog_rows=values(binlog_rows), old_rows=values(old_rows), "
                            + "output_rows=values(output_rows), target_partitions=values(target_partitions), audit_path=values(audit_path)",
                    status.getSourceDatabase(),
                    status.getSourceTable(),
                    status.getProcessDt(),
                    status.getRunId(),
                    status.getStatus(),
                    status.getBinlogRows(),
                    status.getOldRows(),
                    status.getOutputRows(),
                    status.getTargetPartitions(),
                    status.getAuditPath()
            );
        } catch (DataAccessException ignored) {
        }
    }

    public List<MergeTaskStatus> findLatest(int limit) {
        try {
            return jdbcTemplate.query(
                    "select * from merge_task_status order by updated_at desc, id desc limit ?",
                    (rs, rowNum) -> {
                        MergeTaskStatus item = new MergeTaskStatus();
                        item.setId(rs.getLong("id"));
                        item.setSourceDatabase(rs.getString("source_database"));
                        item.setSourceTable(rs.getString("source_table"));
                        item.setProcessDt(rs.getString("process_dt"));
                        item.setRunId(rs.getString("run_id"));
                        item.setStatus(rs.getString("status"));
                        item.setBinlogRows(rs.getInt("binlog_rows"));
                        item.setOldRows(rs.getInt("old_rows"));
                        item.setOutputRows(rs.getInt("output_rows"));
                        item.setTargetPartitions(rs.getString("target_partitions"));
                        item.setAuditPath(rs.getString("audit_path"));
                        item.setUpdatedAt(String.valueOf(rs.getTimestamp("updated_at")));
                        return item;
                    },
                    limit
            );
        } catch (DataAccessException ex) {
            return Collections.emptyList();
        }
    }
}
