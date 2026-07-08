package com.example.warehouse.service;

import com.example.warehouse.model.TableMetadata;
import com.example.warehouse.model.CommandResult;
import com.example.warehouse.model.OnboardRequest;
import com.example.warehouse.model.SparkTaskConfig;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.File;
import java.util.Arrays;
import java.util.List;
import java.util.stream.Collectors;
import org.springframework.stereotype.Service;

@Service
public class OnboardingService {
    private final CommandExecutorService commandExecutorService;
    private final TaskConfigService taskConfigService;
    private final MetadataService metadataService;
    private final ObjectMapper objectMapper = new ObjectMapper();

    public OnboardingService(CommandExecutorService commandExecutorService, TaskConfigService taskConfigService, MetadataService metadataService) {
        this.commandExecutorService = commandExecutorService;
        this.taskConfigService = taskConfigService;
        this.metadataService = metadataService;
    }

    public List<String> buildPlan(OnboardRequest request) {
        String code = request.getDatabaseName() + "." + request.getTableName();
        return Arrays.asList(
                "Pull DBA metadata for " + code,
                "Generate metadata/tables/" + code + ".json",
                "Generate ods_binlog DDL",
                "Generate ods snapshot DDL",
                "Generate SparkSQL merge SQL",
                "Generate DolphinScheduler merge task",
                "Bootstrap MySQL full data into ods_binlog",
                "Replace ODS initial snapshot from MySQL full data"
        );
    }

    public CommandResult execute(OnboardRequest request) {
        CommandResult result = commandExecutorService.run(
                Arrays.asList(
                        "python3",
                        "scripts/onboard_table.py",
                        request.getDbaMetadataPath(),
                        request.getPrimaryKeys(),
                        request.getVersionColumn(),
                        request.getPartitionColumn(),
                        "--bootstrap",
                        "--merge-bootstrap"
                ),
                180
        );
        if (result.getExitCode() == 0) {
            metadataService.saveTable(buildMetadata(request));
            SparkTaskConfig task = new SparkTaskConfig();
            String odsTable = "ods_" + request.getDatabaseName() + "_" + request.getTableName() + "_dic";
            task.setTaskName("merge_" + odsTable);
            task.setTaskType("SparkSQL");
            task.setCommand("spark-sql -f warehouse/sql/ods/merge/merge_" + odsTable + ".sql");
            task.setSchedule("0 30 2 * * ?");
            taskConfigService.saveTask(task);
        }
        return result;
    }

    private TableMetadata buildMetadata(OnboardRequest request) {
        TableMetadata table = new TableMetadata();
        String database = request.getDatabaseName();
        String sourceTable = request.getTableName();
        table.setDatabaseName(database);
        table.setTableName(sourceTable);
        table.setOdsBinlogTable("ods_binlog_" + database + "_" + sourceTable + "_di");
        table.setOdsTable("ods_" + database + "_" + sourceTable + "_dic");
        table.setPrimaryKeys(Arrays.stream(request.getPrimaryKeys().split(",")).map(String::trim).collect(Collectors.toList()));
        table.setVersionColumn(request.getVersionColumn());
        table.setPartitionColumn(request.getPartitionColumn());
        table.setColumnsJson(readColumnsJson(request));
        return table;
    }

    private String readColumnsJson(OnboardRequest request) {
        try {
            File dbaFile = new File(commandExecutorService.getProjectRoot(), request.getDbaMetadataPath());
            JsonNode root = objectMapper.readTree(dbaFile);
            return objectMapper.writeValueAsString(root.get("columns"));
        } catch (Exception ex) {
            return "[]";
        }
    }
}
