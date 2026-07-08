package com.example.warehouse.service;

import com.example.warehouse.model.TableMetadata;
import com.example.warehouse.repository.TableMetadataRepository;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.File;
import java.io.IOException;
import java.util.Collections;
import java.util.List;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

@Service
public class MetadataService {
    private static final Logger log = LoggerFactory.getLogger(MetadataService.class);
    private static final String FALLBACK_PATH = "data/platform/table_metadata.json";

    private final TableMetadataRepository tableMetadataRepository;
    private final ObjectMapper objectMapper;

    public MetadataService(TableMetadataRepository tableMetadataRepository, ObjectMapper objectMapper) {
        this.tableMetadataRepository = tableMetadataRepository;
        this.objectMapper = objectMapper;
    }

    public List<TableMetadata> listTables() {
        List<TableMetadata> tables = tableMetadataRepository.findAllEnabled();
        if (!tables.isEmpty()) {
            return tables;
        }
        log.info("MySQL not available, reading from local fallback: {}", FALLBACK_PATH);
        return loadFromJsonFile();
    }

    private List<TableMetadata> loadFromJsonFile() {
        File file = new File(FALLBACK_PATH);
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
}
