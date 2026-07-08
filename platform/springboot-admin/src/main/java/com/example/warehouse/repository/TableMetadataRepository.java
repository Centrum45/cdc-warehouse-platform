package com.example.warehouse.repository;

import com.example.warehouse.model.TableMetadata;
import java.util.Arrays;
import java.util.List;
import java.util.stream.Collectors;
import org.springframework.dao.DataAccessException;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.core.RowMapper;
import org.springframework.stereotype.Repository;

@Repository
public class TableMetadataRepository {
    private final JdbcTemplate jdbcTemplate;

    public TableMetadataRepository(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }

    private final RowMapper<TableMetadata> rowMapper = (rs, rowNum) -> {
        TableMetadata table = new TableMetadata();
        table.setId(rs.getLong("id"));
        table.setDatabaseName(rs.getString("source_database"));
        table.setTableName(rs.getString("source_table"));
        table.setOdsBinlogTable(rs.getString("ods_binlog_table"));
        table.setOdsTable(rs.getString("ods_table"));
        table.setPrimaryKeys(splitCsv(rs.getString("primary_keys")));
        table.setVersionColumn(rs.getString("version_column"));
        table.setPartitionColumn(rs.getString("partition_column"));
        table.setColumnsJson(rs.getString("columns_json"));
        return table;
    };

    public List<TableMetadata> findAllEnabled() {
        try {
            return jdbcTemplate.query(
                    "select * from table_metadata where enabled = 1 order by source_database, source_table",
                    rowMapper
            );
        } catch (DataAccessException ex) {
            return java.util.Collections.emptyList();
        }
    }

    public void upsert(TableMetadata table) {
        try {
            jdbcTemplate.update(
                    "insert into table_metadata (source_database, source_table, ods_binlog_table, ods_table, primary_keys, version_column, partition_column, columns_json) "
                            + "values (?, ?, ?, ?, ?, ?, ?, ?) "
                            + "on duplicate key update ods_binlog_table=values(ods_binlog_table), ods_table=values(ods_table), primary_keys=values(primary_keys), "
                            + "version_column=values(version_column), partition_column=values(partition_column), columns_json=values(columns_json), enabled=1",
                    table.getDatabaseName(),
                    table.getTableName(),
                    table.getOdsBinlogTable(),
                    table.getOdsTable(),
                    String.join(",", table.getPrimaryKeys()),
                    table.getVersionColumn(),
                    table.getPartitionColumn(),
                    table.getColumnsJson()
            );
        } catch (DataAccessException ignored) {
        }
    }

    private static List<String> splitCsv(String value) {
        return Arrays.stream(value.split(","))
                .map(String::trim)
                .filter(item -> !item.isEmpty())
                .collect(Collectors.toList());
    }
}
