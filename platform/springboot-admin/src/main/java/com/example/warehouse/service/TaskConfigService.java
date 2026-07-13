package com.example.warehouse.service;

import com.example.warehouse.config.WarehouseProperties;
import com.example.warehouse.model.CommandResult;
import com.example.warehouse.model.SparkTaskConfig;
import com.example.warehouse.model.TaskExecution;
import com.example.warehouse.repository.TaskExecutionRepository;
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
    private final CommandExecutorService commandExecutorService;
    private final WarehouseProperties warehouseProperties;
    private final TaskExecutionRepository taskExecutionRepository;

    public TaskConfigService(TaskRepository taskRepository,
                             ObjectMapper objectMapper,
                             CommandExecutorService commandExecutorService,
                             WarehouseProperties warehouseProperties,
                             TaskExecutionRepository taskExecutionRepository) {
        this.taskRepository = taskRepository;
        this.objectMapper = objectMapper;
        this.commandExecutorService = commandExecutorService;
        this.warehouseProperties = warehouseProperties;
        this.taskExecutionRepository = taskExecutionRepository;
    }

    public List<SparkTaskConfig> listTasks() {
        List<SparkTaskConfig> tasks = taskRepository.findEnabledTasks();
        if (!tasks.isEmpty()) {
            return tasks;
        }
        if (!warehouseProperties.getMysql().isFallbackDemoData()) {
            throw new IllegalStateException("No task config from MySQL and fallback is disabled");
        }
        log.info("MySQL task config unavailable or empty, reading local fallback: {}", FALLBACK_PATH);
        return loadFromJsonFile();
    }

    private List<SparkTaskConfig> loadFromJsonFile() {
        File file = new File(commandExecutorService.getProjectRoot(), FALLBACK_PATH);
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

    public CommandResult runTask(String taskName) {
        return listTasks().stream()
                .filter(task -> taskName.equals(task.getTaskName()))
                .findFirst()
                .map(this::runAndRecord)
                .orElseGet(() -> new CommandResult(2, "task not found: " + taskName));
    }

    public CommandResult rerunExecution(long executionId) {
        return taskExecutionRepository.findById(executionId)
                .map(this::rerunAndRecord)
                .orElseGet(() -> new CommandResult(2, "task execution not found: " + executionId));
    }

    private CommandResult runAndRecord(SparkTaskConfig task) {
        long startedAt = System.currentTimeMillis();
        CommandResult result = commandExecutorService.run(java.util.Arrays.asList("bash", "-lc", task.getCommand()), 600);
        long durationMs = System.currentTimeMillis() - startedAt;
        taskExecutionRepository.save(
                task.getTaskName(),
                task.getTaskType(),
                task.getCommand(),
                result.getExitCode(),
                result.getOutput(),
                durationMs
        );
        return result;
    }

    private CommandResult rerunAndRecord(TaskExecution execution) {
        long startedAt = System.currentTimeMillis();
        CommandResult result = commandExecutorService.run(java.util.Arrays.asList("bash", "-lc", execution.getCommand()), 600);
        long durationMs = System.currentTimeMillis() - startedAt;
        taskExecutionRepository.save(
                execution.getTaskName(),
                execution.getTaskType(),
                execution.getCommand(),
                result.getExitCode(),
                result.getOutput(),
                durationMs
        );
        return result;
    }
}
