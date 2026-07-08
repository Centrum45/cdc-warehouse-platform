package com.example.warehouse.service;

import com.example.warehouse.model.MonitorResult;
import com.example.warehouse.repository.MonitorResultRepository;
import java.util.Arrays;
import java.util.List;
import org.springframework.stereotype.Service;

@Service
public class MonitorService {
    private final MonitorResultRepository monitorResultRepository;

    public MonitorService(MonitorResultRepository monitorResultRepository) {
        this.monitorResultRepository = monitorResultRepository;
    }

    public List<String> listMonitorItems() {
        return Arrays.asList("delay", "field", "special_value", "table_update", "plaintext");
    }

    public List<MonitorResult> listLatestResults() {
        return monitorResultRepository.findLatest();
    }
}
