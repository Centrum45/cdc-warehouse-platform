package com.example.warehouse.service;

import com.example.warehouse.model.SparkTaskConfig;
import com.example.warehouse.repository.TaskRepository;
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
public class TaskConfigService {
    private static final Logger log = LoggerFactory.getLogger(TaskConfigService.class);
    private static final String FALLBACK_PATH = "data/platform/task_configs.json";

    private final TaskRepository taskRepository;
    private final ObjectMapper objectMapper;

    public TaskConfigService(TaskRepository taskRepository, ObjectMapper objectMapper) {
        this.taskRepository = taskRepository;
        this.objectMapper = objectMapper;
    }

    public List<SparkTaskConfig> listTasks() {
        List<SparkTaskConfig> tasks = taskRepository.findEnabledTasks();
        if (!tasks.isEmpty()) {
            return tasks;
        }
        log.info("MySQL not available, reading from local fallback: {}", FALLBACK_PATH);
        return loadFromJsonFile();
    }

    private List<SparkTaskConfig> loadFromJsonFile() {
        File file = new File(FALLBACK_PATH);
        if (!file.exists()) {
            log.warn("Fallback file not found: {}", FALLBACK_PATH);
            return Collections.emptyList();
        }
        try {
            return objectMapper.readValue(file, new TypeReference<List<SparkTaskConfig>>() {});
        } catch (IOException e) {
            log.error("Failed to read fallback tasks: {}", e.getMessage());
            return Collections.emptyList();
        }
    }

    public void saveTask(SparkTaskConfig task) {
        taskRepository.upsert(task);
    }
}
