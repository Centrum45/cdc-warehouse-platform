package com.example.warehouse.service;

import com.example.warehouse.config.WarehouseProperties;
import com.example.warehouse.model.RuleRecord;
import com.example.warehouse.repository.RuleRepository;
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
public class RuleService {
    private static final Logger log = LoggerFactory.getLogger(RuleService.class);
    private static final String FALLBACK_PATH = "data/platform/sensitive_rules.json";

    private final RuleRepository ruleRepository;
    private final ObjectMapper objectMapper;
    private final CommandExecutorService commandExecutorService;
    private final WarehouseProperties warehouseProperties;

    public RuleService(RuleRepository ruleRepository, ObjectMapper objectMapper, CommandExecutorService commandExecutorService, WarehouseProperties warehouseProperties) {
        this.ruleRepository = ruleRepository;
        this.objectMapper = objectMapper;
        this.commandExecutorService = commandExecutorService;
        this.warehouseProperties = warehouseProperties;
    }

    public List<RuleRecord> listRules() {
        List<RuleRecord> rules = ruleRepository.findAll();
        if (!rules.isEmpty()) {
            return rules;
        }
        if (!warehouseProperties.getMysql().isFallbackDemoData()) {
            throw new IllegalStateException("No sensitive rules from MySQL and fallback is disabled");
        }
        log.info("MySQL sensitive rules unavailable or empty, reading local fallback: {}", FALLBACK_PATH);
        return loadFromJsonFile();
    }

    private List<RuleRecord> loadFromJsonFile() {
        File file = new File(commandExecutorService.getProjectRoot(), FALLBACK_PATH);
        if (!file.exists()) {
            log.warn("Fallback file not found: {}", FALLBACK_PATH);
            return Collections.emptyList();
        }
        try {
            return objectMapper.readValue(file, new TypeReference<List<RuleRecord>>() {});
        } catch (IOException e) {
            log.error("Failed to read fallback rules: {}", e.getMessage());
            return Collections.emptyList();
        }
    }

    public void saveSensitive(RuleRecord rule) {
        ruleRepository.saveSensitive(rule);
    }
}
