package com.example.warehouse.service;

import com.example.warehouse.model.MonitorResult;
import com.example.warehouse.repository.MonitorResultRepository;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.File;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

@Service
public class MonitorService {
    private static final Logger log = LoggerFactory.getLogger(MonitorService.class);
    private static final String FALLBACK_PATH = "data/platform/monitor_items.json";

    private final MonitorResultRepository monitorResultRepository;
    private final ObjectMapper objectMapper;

    public MonitorService(MonitorResultRepository monitorResultRepository, ObjectMapper objectMapper) {
        this.monitorResultRepository = monitorResultRepository;
        this.objectMapper = objectMapper;
    }

    public List<String> listMonitorItems() {
        File file = new File(FALLBACK_PATH);
        if (!file.exists()) {
            log.info("Fallback file not found, returning built-in list");
            return getBuiltInMonitorTypes();
        }
        try {
            Map<String, Object> root = objectMapper.readValue(file, new TypeReference<Map<String, Object>>() {});
            @SuppressWarnings("unchecked")
            List<Map<String, Object>> monitors = (List<Map<String, Object>>) root.get("monitors");
            if (monitors == null) {
                return getBuiltInMonitorTypes();
            }
            List<String> types = new ArrayList<>();
            for (Map<String, Object> m : monitors) {
                Object type = m.get("monitorType");
                if (type != null) {
                    types.add(type.toString());
                }
            }
            return types;
        } catch (IOException e) {
            log.error("Failed to read fallback monitors: {}", e.getMessage());
            return getBuiltInMonitorTypes();
        }
    }

    private List<String> getBuiltInMonitorTypes() {
        List<String> types = new ArrayList<>();
        types.add("delay");
        types.add("field");
        types.add("special_value");
        types.add("table_update");
        types.add("plaintext");
        types.add("row_count");
        types.add("null_rate");
        types.add("partition");
        return types;
    }

    public List<MonitorResult> listLatestResults() {
        return monitorResultRepository.findLatest();
    }
}
