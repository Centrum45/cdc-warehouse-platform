package com.example.warehouse.service;

import com.example.warehouse.model.TableMetadata;
import com.example.warehouse.repository.TableMetadataRepository;
import java.util.Arrays;
import java.util.List;
import org.springframework.stereotype.Service;

@Service
public class MetadataService {
    private final TableMetadataRepository tableMetadataRepository;

    public MetadataService(TableMetadataRepository tableMetadataRepository) {
        this.tableMetadataRepository = tableMetadataRepository;
    }

    public List<TableMetadata> listTables() {
        List<TableMetadata> tables = tableMetadataRepository.findAllEnabled();
        if (!tables.isEmpty()) {
            return tables;
        }
        TableMetadata table = new TableMetadata();
        table.setId(1L);
        table.setDatabaseName("basiccomment");
        table.setTableName("avatar_commentbatchsource");
        table.setOdsBinlogTable("ods_binlog_basiccomment_avatar_commentbatchsource_di");
        table.setOdsTable("ods_basiccomment_avatar_commentbatchsource_dic");
        table.setPrimaryKeys(Arrays.asList("id"));
        table.setVersionColumn("ver");
        table.setPartitionColumn("ctime");
        table.setColumnsJson("[{\"name\":\"id\",\"type\":\"bigint\"}]");
        return Arrays.asList(table);
    }

    public void saveTable(TableMetadata table) {
        tableMetadataRepository.upsert(table);
    }
}
