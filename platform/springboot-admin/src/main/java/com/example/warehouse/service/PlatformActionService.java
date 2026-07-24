package com.example.warehouse.service;

import com.example.warehouse.model.ActionRequest;
import com.example.warehouse.model.CommandResult;
import com.example.warehouse.repository.TaskExecutionRepository;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import org.springframework.stereotype.Service;

@Service
public class PlatformActionService {
    private final CommandExecutorService commandExecutorService;
    private final TaskExecutionRepository taskExecutionRepository;

    public PlatformActionService(CommandExecutorService commandExecutorService,
                                 TaskExecutionRepository taskExecutionRepository) {
        this.commandExecutorService = commandExecutorService;
        this.taskExecutionRepository = taskExecutionRepository;
    }

    public CommandResult run(String action, ActionRequest request) {
        if ("refresh-ops".equals(action)) {
            return commandExecutorService.run(Arrays.asList("bash", "scripts/refresh_ops_snapshot.sh"), 60);
        }
        if ("daily-merge".equals(action)) {
            List<String> command = new ArrayList<>();
            command.add("bash");
            command.add("deploy/run_job.sh");
            command.add("daily-merge");
            if (request != null && notBlank(request.getBizDt())) {
                command.add(request.getBizDt().trim());
            }
            return commandExecutorService.run(command, 300);
        }
        if ("monitor-suite".equals(action)) {
            List<String> command = new ArrayList<>();
            command.add("bash");
            command.add("deploy/run_job.sh");
            command.add("monitors");
            if (request != null && notBlank(request.getBizDt())) {
                command.add(request.getBizDt().trim());
            }
            return commandExecutorService.run(command, 1800);
        }
        if ("test-alert".equals(action)) {
            return commandExecutorService.run(Arrays.asList("python3", "scripts/send_test_alert.py"), 60);
        }
        if ("ds-publish".equals(action)) {
            String mode = request == null || !notBlank(request.getMode()) ? "--audit" : request.getMode().trim();
            if (!"--audit".equals(mode) && !"--dry-run".equals(mode) && !"--live".equals(mode)) {
                return new CommandResult(2, "invalid mode: " + mode);
            }
            return commandExecutorService.run(Arrays.asList("python3", "scripts/publish_dolphinscheduler.py", mode), 120);
        }
        if ("realtime-kafka-kudu-once".equals(action)) {
            return commandExecutorService.run(Arrays.asList(
                    "python3",
                    "scripts/spark_streaming_kafka_to_kudu_once.py",
                    "--bootstrap-objects"), 180);
        }
        if ("verify-e2e-local".equals(action)) {
            List<String> command = new ArrayList<>();
            command.add("bash");
            command.add("scripts/verify_end_to_end.sh");
            command.add("--mode");
            command.add("local");
            if (request != null && notBlank(request.getBizDt())) {
                command.add("--biz-dt");
                command.add(request.getBizDt().trim());
            }
            return runAndRecord("verify-e2e-local", "VERIFY", command, 1800);
        }
        if ("verify-e2e-server".equals(action)) {
            List<String> command = new ArrayList<>();
            command.add("bash");
            command.add("scripts/verify_end_to_end.sh");
            command.add("--mode");
            command.add("server");
            if (request != null && notBlank(request.getBizDt())) {
                command.add("--biz-dt");
                command.add(request.getBizDt().trim());
            }
            return runAndRecord("verify-e2e-server", "VERIFY", command, 900);
        }
        return new CommandResult(2, "unknown action: " + action);
    }

    private CommandResult runAndRecord(String taskName, String taskType, List<String> command, long timeoutSeconds) {
        long startedAt = System.currentTimeMillis();
        CommandResult result = commandExecutorService.run(command, timeoutSeconds);
        long durationMs = System.currentTimeMillis() - startedAt;
        taskExecutionRepository.save(
                taskName,
                taskType,
                String.join(" ", command),
                result.getExitCode(),
                result.getOutput(),
                durationMs
        );
        return result;
    }

    private boolean notBlank(String value) {
        return value != null && !value.trim().isEmpty();
    }
}
