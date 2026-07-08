package com.example.warehouse.repository;

import com.example.warehouse.model.RuleRecord;
import java.util.ArrayList;
import java.util.List;
import org.springframework.dao.DataAccessException;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Repository;

@Repository
public class RuleRepository {
    private final JdbcTemplate jdbcTemplate;

    public RuleRepository(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }

    public List<RuleRecord> findAll() {
        List<RuleRecord> result = new ArrayList<>();
        try {
            result.addAll(jdbcTemplate.query(
                    "select id, column_pattern, action, default_value from sensitive_rule where enabled = 1 order by id",
                    (rs, rowNum) -> {
                        RuleRecord rule = new RuleRecord();
                        rule.setId(rs.getLong("id"));
                        rule.setRuleCategory("sensitive");
                        rule.setColumnName(rs.getString("column_pattern"));
                        rule.setAction(rs.getString("action"));
                        rule.setRuleValue(rs.getString("default_value"));
                        return rule;
                    }
            ));
            result.addAll(jdbcTemplate.query(
                    "select id, source_database, source_table, column_name, rule_type, rule_value from special_value_rule where enabled = 1 order by id",
                    (rs, rowNum) -> {
                        RuleRecord rule = new RuleRecord();
                        rule.setId(rs.getLong("id"));
                        rule.setRuleCategory("special");
                        rule.setDatabaseName(rs.getString("source_database"));
                        rule.setTableName(rs.getString("source_table"));
                        rule.setColumnName(rs.getString("column_name"));
                        rule.setRuleType(rs.getString("rule_type"));
                        rule.setRuleValue(rs.getString("rule_value"));
                        return rule;
                    }
            ));
        } catch (DataAccessException ignored) {
        }
        return result;
    }

    public void saveSensitive(RuleRecord rule) {
        try {
            jdbcTemplate.update(
                    "insert into sensitive_rule (column_pattern, action, default_value, enabled) values (?, ?, ?, 1) "
                            + "on duplicate key update action=values(action), default_value=values(default_value), enabled=1",
                    rule.getColumnName(), rule.getAction(), rule.getRuleValue()
            );
        } catch (DataAccessException ignored) {
        }
    }
}
