package com.example.warehouse.repository;

import com.example.warehouse.model.SparkTaskConfig;
import java.util.List;
import org.springframework.dao.DataAccessException;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Repository;

@Repository
public class TaskRepository {
    private final JdbcTemplate jdbcTemplate;

    public TaskRepository(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }

    public List<SparkTaskConfig> findEnabledTasks() {
        try {
            return jdbcTemplate.query(
                    "select task_name, task_type, command, schedule_expr from sync_task where enabled = 1 order by id",
                    (rs, rowNum) -> {
                        SparkTaskConfig task = new SparkTaskConfig();
                        task.setTaskName(rs.getString("task_name"));
                        task.setTaskType(rs.getString("task_type"));
                        task.setCommand(rs.getString("command"));
                        task.setSchedule(rs.getString("schedule_expr"));
                        return task;
                    }
            );
        } catch (DataAccessException ex) {
            return java.util.Collections.emptyList();
        }
    }

    public void upsert(SparkTaskConfig task) {
        try {
            jdbcTemplate.update(
                    "insert into sync_task (task_name, task_type, command, schedule_expr, enabled) values (?, ?, ?, ?, 1) "
                            + "on duplicate key update task_type=values(task_type), command=values(command), schedule_expr=values(schedule_expr), enabled=1",
                    task.getTaskName(),
                    task.getTaskType(),
                    task.getCommand(),
                    task.getSchedule()
            );
        } catch (DataAccessException ignored) {
        }
    }
}
