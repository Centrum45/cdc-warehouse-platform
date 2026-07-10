package com.example.warehouse.service;

import com.example.warehouse.config.WarehouseProperties;
import com.example.warehouse.model.TableMetadata;
import com.example.warehouse.repository.TableMetadataRepository;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.File;
import java.io.IOException;
import java.util.Collections;
import java.util.List;
import java.util.Optional;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

@Service
public class MetadataService {
    private static final Logger log = LoggerFactory.getLogger(MetadataService.class);
    private static final String FALLBACK_PATH = "data/platform/table_metadata.json";

    private final TableMetadataRepository tableMetadataRepository;
    private final ObjectMapper objectMapper;
    private final CommandExecutorService commandExecutorService;
    private final WarehouseProperties warehouseProperties;

    public MetadataService(TableMetadataRepository tableMetadataRepository, ObjectMapper objectMapper, CommandExecutorService commandExecutorService, WarehouseProperties warehouseProperties) {
        this.tableMetadataRepository = tableMetadataRepository;
        this.objectMapper = objectMapper;
        this.commandExecutorService = commandExecutorService;
        this.warehouseProperties = warehouseProperties;
    }

    public List<TableMetadata> listTables() {
        List<TableMetadata> tables = tableMetadataRepository.findAllEnabled();
        if (!tables.isEmpty()) {
            return tables;
        }
        if (!warehouseProperties.getMysql().isFallbackDemoData()) {
            throw new IllegalStateException("No table metadata from MySQL and fallback is disabled");
        }
        log.info("MySQL metadata unavailable or empty, reading local fallback: {}", FALLBACK_PATH);
        return loadFromJsonFile();
    }

    private List<TableMetadata> loadFromJsonFile() {
        File file = new File(commandExecutorService.getProjectRoot(), FALLBACK_PATH);
        if (!file.exists()) {
            log.warn("Fallback file not found: {}", FALLBACK_PATH);
            return Collections.emptyList();
        }
        try {
            return objectMapper.readValue(file, new TypeReference<List<TableMetadata>>() {});
        } catch (IOException e) {
            log.error("Failed to read fallback metadata: {}", e.getMessage());
            return Collections.emptyList();
        }
    }

    public void saveTable(TableMetadata table) {
        tableMetadataRepository.upsert(table);
    }

    public Optional<TableMetadata> findTable(String databaseName, String tableName) {
        Optional<TableMetadata> fromMysql = tableMetadataRepository.findEnabled(databaseName, tableName);
        if (fromMysql.isPresent()) {
            return fromMysql;
        }
        if (!warehouseProperties.getMysql().isFallbackDemoData()) {
            return Optional.empty();
        }
        return loadFromJsonFile().stream()
                .filter(table -> databaseName.equals(table.getDatabaseName()) && tableName.equals(table.getTableName()))
                .findFirst();
    }
}
