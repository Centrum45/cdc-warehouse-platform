package com.example.warehouse.service;

import com.example.warehouse.model.CommandResult;
import com.example.warehouse.model.TableMetadata;
import com.example.warehouse.model.TableOpsRequest;
import com.example.warehouse.repository.MonitorResultRepository;
import com.example.warehouse.repository.TaskExecutionRepository;
import java.time.LocalDate;
import java.util.Arrays;
import java.util.List;
import java.util.Optional;
import org.springframework.stereotype.Service;

@Service
public class TableOpsService {
    private final MetadataService metadataService;
    private final CommandExecutorService commandExecutorService;
    private final TaskExecutionRepository taskExecutionRepository;
    private final MonitorResultRepository monitorResultRepository;

    public TableOpsService(MetadataService metadataService,
                           CommandExecutorService commandExecutorService,
                           TaskExecutionRepository taskExecutionRepository,
                           MonitorResultRepository monitorResultRepository) {
        this.metadataService = metadataService;
        this.commandExecutorService = commandExecutorService;
        this.taskExecutionRepository = taskExecutionRepository;
        this.monitorResultRepository = monitorResultRepository;
    }

    public CommandResult backfill(TableOpsRequest request) {
        Optional<TableMetadata> table = findTable(request);
        if (!table.isPresent()) {
            return new CommandResult(2, "table metadata not found");
        }
        String start = valueOrDefault(request.getStartDt(), valueOrDefault(request.getBizDt(), LocalDate.now().minusDays(1).toString()));
        String end = valueOrDefault(request.getEndDt(), start);
        String command = "bash scripts/table_ops.sh backfill "
                + q(table.get().getDatabaseName()) + " "
                + q(table.get().getTableName()) + " "
                + q(start) + " "
                + q(end);
        return runAndRecord("backfill_" + request.getDatabaseName() + "_" + request.getTableName(), "BACKFILL", command, 1800, request);
    }

    public CommandResult checkLineage(TableOpsRequest request) {
        Optional<TableMetadata> table = findTable(request);
        if (!table.isPresent()) {
            return new CommandResult(2, "table metadata not found");
        }
        String dt = valueOrDefault(request.getBizDt(), LocalDate.now().minusDays(1).toString());
        String command = "bash scripts/table_ops.sh check-lineage "
                + q(table.get().getDatabaseName()) + " "
                + q(table.get().getTableName()) + " "
                + q(dt) + " "
                + q(table.get().getOdsTable());
        return runAndRecord("check_lineage_" + request.getDatabaseName() + "_" + request.getTableName(), "CHECK", command, 300, request);
    }

    public CommandResult consistency(TableOpsRequest request) {
        Optional<TableMetadata> table = findTable(request);
        if (!table.isPresent()) {
            return new CommandResult(2, "table metadata not found");
        }
        String dt = valueOrDefault(request.getBizDt(), LocalDate.now().minusDays(1).toString());
        String command = "bash scripts/table_ops.sh consistency "
                + q(table.get().getDatabaseName()) + " "
                + q(table.get().getTableName()) + " "
                + q(dt) + " "
                + q(table.get().getOdsTable()) + " "
                + q(table.get().getPartitionColumn());
        CommandResult result = runAndRecord("consistency_" + request.getDatabaseName() + "_" + request.getTableName(), "MONITOR", command, 300, request);
        if (isDryRun(request)) {
            return result;
        }
        monitorResultRepository.save(
                "row_count_consistency",
                table.get().getDatabaseName(),
                table.get().getTableName(),
                result.getExitCode() == 0 ? "OK" : "WARN",
                result.getOutput(),
                "dt=" + dt
        );
        return result;
    }

    public CommandResult onboardingVerify(TableOpsRequest request) {
        Optional<TableMetadata> table = findTable(request);
        if (!table.isPresent()) {
            return new CommandResult(2, "table metadata not found. Run onboarding first.");
        }
        String dt = valueOrDefault(request.getBizDt(), valueOrDefault(request.getStartDt(), LocalDate.now().minusDays(1).toString()));
        String command = "bash scripts/table_ops.sh onboarding-verify "
                + q(table.get().getDatabaseName()) + " "
                + q(table.get().getTableName()) + " "
                + q(dt) + " "
                + q(table.get().getOdsTable());
        return runAndRecord("onboarding_verify_" + request.getDatabaseName() + "_" + request.getTableName(), "VERIFY", command, 1800, request);
    }

    public List<TableMetadata> listTables() {
        return metadataService.listTables();
    }

    private Optional<TableMetadata> findTable(TableOpsRequest request) {
        return metadataService.findTable(request.getDatabaseName(), request.getTableName());
    }

    private CommandResult runAndRecord(String taskName, String taskType, String command, long timeoutSeconds, TableOpsRequest request) {
        if (isDryRun(request)) {
            String output = "DRY RUN\n\n" + command;
            taskExecutionRepository.save(taskName, taskType, command, 0, output, 0L);
            return new CommandResult(0, output);
        }
        long startedAt = System.currentTimeMillis();
        CommandResult result = commandExecutorService.run(Arrays.asList("bash", "-lc", command), timeoutSeconds);
        long durationMs = System.currentTimeMillis() - startedAt;
        taskExecutionRepository.save(taskName, taskType, command, result.getExitCode(), result.getOutput(), durationMs);
        return result;
    }

    private String valueOrDefault(String value, String fallback) {
        return value == null || value.trim().isEmpty() ? fallback : value.trim();
    }

    private boolean isDryRun(TableOpsRequest request) {
        return request != null && Boolean.TRUE.equals(request.getDryRun());
    }

    private String shell(String value) {
        return value == null ? "" : value.replace("'", "'\"'\"'");
    }

    private String q(String value) {
        return "'" + shell(value) + "'";
    }
}
