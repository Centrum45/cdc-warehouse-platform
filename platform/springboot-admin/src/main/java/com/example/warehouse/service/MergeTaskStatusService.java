package com.example.warehouse.service;

import com.example.warehouse.model.MergeTaskStatus;
import com.example.warehouse.repository.MergeTaskStatusRepository;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.File;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

@Service
public class MergeTaskStatusService {
    private final MergeTaskStatusRepository repository;
    private final CommandExecutorService commandExecutorService;
    private final ObjectMapper objectMapper;
    private final String auditRoot;

    public MergeTaskStatusService(MergeTaskStatusRepository repository,
                                  CommandExecutorService commandExecutorService,
                                  ObjectMapper objectMapper,
                                  @Value("${warehouse.merge.audit-root:${MERGE_AUDIT_ROOT:data/ops/merge_audit}}") String auditRoot) {
        this.repository = repository;
        this.commandExecutorService = commandExecutorService;
        this.objectMapper = objectMapper;
        this.auditRoot = auditRoot;
    }

    public List<MergeTaskStatus> latest() {
        syncAuditFiles();
        return repository.findLatest(50);
    }

    public void syncAuditFiles() {
        File root = new File(auditRoot);
        if (!root.isAbsolute()) {
            root = new File(commandExecutorService.getProjectRoot(), auditRoot);
        }
        File[] files = root.listFiles((dir, name) -> name.endsWith(".json"));
        if (files == null) {
            return;
        }
        for (File file : files) {
            syncOne(file);
        }
    }

    private void syncOne(File file) {
        try {
            JsonNode root = objectMapper.readTree(file);
            MergeTaskStatus status = new MergeTaskStatus();
            status.setSourceDatabase(text(root, "database"));
            status.setSourceTable(text(root, "table"));
            status.setProcessDt(text(root, "process_dt"));
            status.setRunId(text(root, "run_id"));
            status.setStatus(text(root, "status"));
            status.setAuditPath(relativePath(file));

            int binlogRows = 0;
            int oldRows = 0;
            int outputRows = 0;
            List<String> partitions = new ArrayList<>();
            JsonNode partitionNodes = root.get("partitions");
            if (partitionNodes != null && partitionNodes.isArray()) {
                for (JsonNode partition : partitionNodes) {
                    binlogRows += integer(partition, "binlog_rows");
                    oldRows += integer(partition, "old_rows");
                    outputRows += integer(partition, "output_rows");
                    String dt = text(partition, "dt");
                    if (!dt.isEmpty()) {
                        partitions.add(dt);
                    }
                }
            }
            status.setBinlogRows(binlogRows);
            status.setOldRows(oldRows);
            status.setOutputRows(outputRows);
            status.setTargetPartitions(String.join(",", partitions));
            if (!status.getSourceDatabase().isEmpty() && !status.getSourceTable().isEmpty()
                    && !status.getProcessDt().isEmpty() && !status.getRunId().isEmpty()) {
                repository.upsert(status);
            }
        } catch (IOException ignored) {
        }
    }

    private String text(JsonNode node, String field) {
        JsonNode value = node.get(field);
        return value == null || value.isNull() ? "" : value.asText("");
    }

    private int integer(JsonNode node, String field) {
        JsonNode value = node.get(field);
        return value == null || value.isNull() ? 0 : value.asInt(0);
    }

    private String relativePath(File file) {
        try {
            return commandExecutorService.getProjectRoot().toPath().relativize(file.toPath()).toString();
        } catch (IllegalArgumentException ex) {
            return file.getPath();
        }
    }
}
