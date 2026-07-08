package com.example.warehouse.service;

import com.example.warehouse.model.ActionRequest;
import com.example.warehouse.model.CommandResult;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import org.springframework.stereotype.Service;

@Service
public class PlatformActionService {
    private final CommandExecutorService commandExecutorService;

    public PlatformActionService(CommandExecutorService commandExecutorService) {
        this.commandExecutorService = commandExecutorService;
    }

    public CommandResult run(String action, ActionRequest request) {
        if ("refresh-ops".equals(action)) {
            return commandExecutorService.run(Arrays.asList("bash", "scripts/refresh_ops_snapshot.sh"), 60);
        }
        if ("daily-merge".equals(action)) {
            List<String> command = new ArrayList<>();
            command.add("bash");
            command.add("scripts/run_daily_ods_merge.sh");
            if (request != null && notBlank(request.getBizDt())) {
                command.add(request.getBizDt().trim());
            }
            return commandExecutorService.run(command, 300);
        }
        if ("full-pipeline".equals(action)) {
            List<String> command = Arrays.asList("python3", "warehouse/jobs/run_full_pipeline.py");
            return commandExecutorService.run(command, 180);
        }
        if ("monitor-suite".equals(action)) {
            return commandExecutorService.run(Arrays.asList("python3", "monitors/run_monitor_suite.py"), 120);
        }
        if ("ds-publish".equals(action)) {
            String mode = request == null || !notBlank(request.getMode()) ? "--audit" : request.getMode().trim();
            if (!"--audit".equals(mode) && !"--dry-run".equals(mode) && !"--live".equals(mode)) {
                return new CommandResult(2, "invalid mode: " + mode);
            }
            return commandExecutorService.run(Arrays.asList("python3", "scripts/publish_dolphinscheduler.py", mode), 120);
        }
        return new CommandResult(2, "unknown action: " + action);
    }

    private boolean notBlank(String value) {
        return value != null && !value.trim().isEmpty();
    }
}
