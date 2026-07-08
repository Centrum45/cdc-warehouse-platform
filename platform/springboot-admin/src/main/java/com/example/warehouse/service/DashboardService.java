package com.example.warehouse.service;

import com.example.warehouse.model.CommandResult;
import com.example.warehouse.model.DashboardSnapshot;
import com.example.warehouse.model.TableMetadata;
import com.example.warehouse.model.TableStorageView;
import java.io.BufferedReader;
import java.io.File;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.util.stream.Stream;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Comparator;
import java.util.List;
import org.springframework.stereotype.Service;

@Service
public class DashboardService {
    private final CommandExecutorService commandExecutorService;

    public DashboardService(CommandExecutorService commandExecutorService) {
        this.commandExecutorService = commandExecutorService;
    }

    public DashboardSnapshot snapshot(List<TableMetadata> tables) {
        DashboardSnapshot snapshot = new DashboardSnapshot();
        snapshot.setContainerStatus(readOpsFile("container_status.txt", Arrays.asList("docker", "ps", "--format", "table {{.Names}}\\t{{.Status}}\\t{{.Ports}}")));
        snapshot.setKafkaTopics(readOpsFile("kafka_topics.txt", Arrays.asList("docker", "exec", "cdc-warehouse-kafka", "kafka-topics", "--bootstrap-server", "kafka:9092", "--list")));
        snapshot.setMaxwellLogs(readOpsFile("maxwell.log", Arrays.asList("docker", "logs", "--tail", "120", "cdc-warehouse-maxwell")));
        snapshot.setKafkaLogs(readOpsFile("kafka.log", Arrays.asList("docker", "logs", "--tail", "80", "cdc-warehouse-kafka")));
        snapshot.setSparkStreamingLogs(readOpsFile("spark_streaming.log", Arrays.asList("docker", "logs", "--tail", "80", "cdc-warehouse-spark-streaming")));
        snapshot.setSparkSqlMergeLogs(readOpsFile("spark_sql_merge.log", null));
        snapshot.setAdminLogs(readOpsFile("admin.log", Arrays.asList("docker", "logs", "--tail", "80", "cdc-warehouse-admin")));
        snapshot.setHdfsWarehouseListing(readOpsFile("hdfs_warehouse_ls.txt", Arrays.asList("docker", "exec", "cdc-warehouse-hdfs-namenode", "hdfs", "dfs", "-ls", "-R", "/warehouse")));
        snapshot.setHdfsNamenodeLogs(readOpsFile("hdfs_namenode.log", Arrays.asList("docker", "logs", "--tail", "80", "cdc-warehouse-hdfs-namenode")));
        snapshot.setHiveDatabases(readOpsFile("hive_databases.txt", Arrays.asList("docker", "exec", "cdc-warehouse-hive-server", "beeline", "-u", "jdbc:hive2://localhost:10000", "-e", "show databases;")));
        snapshot.setHiveServerLogs(readOpsFile("hive_server.log", Arrays.asList("docker", "logs", "--tail", "80", "cdc-warehouse-hive-server")));
        snapshot.setRefreshedAt(readOpsFile("refreshed_at.txt", null));
        snapshot.setTableStorage(buildStorageViews(tables));
        return snapshot;
    }

    private String readOpsFile(String name, List<String> fallbackCommand) {
        File file = new File(commandExecutorService.getProjectRoot(), "data/ops/" + name);
        if (file.exists()) {
            return readWhole(file);
        }
        if (fallbackCommand != null) {
            return runCommand(fallbackCommand);
        }
        return "not refreshed";
    }

    private String readWhole(File file) {
        try {
            return new String(Files.readAllBytes(file.toPath()), StandardCharsets.UTF_8);
        } catch (Exception ex) {
            return ex.getMessage();
        }
    }

    private String runCommand(List<String> command) {
        CommandResult result = commandExecutorService.run(command, 15);
        if (result.getExitCode() != 0) {
            return "command failed: " + String.join(" ", command) + "\n" + result.getOutput();
        }
        return result.getOutput();
    }

    private List<TableStorageView> buildStorageViews(List<TableMetadata> tables) {
        List<TableStorageView> views = new ArrayList<>();
        for (TableMetadata table : tables) {
            TableStorageView view = new TableStorageView();
            view.setDatabaseName(table.getDatabaseName());
            view.setTableName(table.getTableName());

            File binlogFile = latestFile("ods_binlog", table.getDatabaseName(), table.getTableName(), "jsonl");
            File odsFile = latestFile("ods", table.getDatabaseName(), table.getTableName(), "csv");
            view.setOdsBinlogPath(displayPath(binlogFile));
            view.setOdsPath(displayPath(odsFile));
            view.setOdsBinlogSample(readHead(binlogFile, 5));
            view.setOdsSample(readHead(odsFile, 8));
            views.add(view);
        }
        return views;
    }

    private File latestFile(String layer, String database, String table, String suffix) {
        File base = new File(commandExecutorService.getProjectRoot(),
                "data/lake/" + layer + "/db=" + database + "/table=" + table);
        if (!base.exists()) {
            return null;
        }
        File[] partitions = base.listFiles(File::isDirectory);
        if (partitions == null || partitions.length == 0) {
            return null;
        }
        Arrays.sort(partitions, Comparator.comparing(File::getName).reversed());
        for (File partition : partitions) {
            File[] files = partition.listFiles((dir, name) -> name.endsWith("." + suffix));
            if (files != null && files.length > 0) {
                Arrays.sort(files, Comparator.comparing(File::getName));
                return files[0];
            }
        }
        return null;
    }

    private String displayPath(File file) {
        if (file == null) {
            return "not generated";
        }
        File root = commandExecutorService.getProjectRoot();
        try {
            return root.toPath().relativize(file.toPath()).toString();
        } catch (Exception ex) {
            return file.getPath();
        }
    }

    private String readHead(File file, int limit) {
        if (file == null || !file.exists()) {
            return "";
        }
        StringBuilder builder = new StringBuilder();
        try (BufferedReader reader = Files.newBufferedReader(file.toPath(), StandardCharsets.UTF_8)) {
            String line;
            int count = 0;
            while ((line = reader.readLine()) != null && count < limit) {
                builder.append(line).append('\n');
                count++;
            }
            try (Stream<String> lines = Files.lines(file.toPath(), StandardCharsets.UTF_8)) {
                long totalLines = lines.count();
                if (totalLines > limit) {
                    builder.append("... ").append(totalLines - limit).append(" more lines\n");
                }
            }
        } catch (Exception ex) {
            return ex.getMessage();
        }
        return builder.toString();
    }
}
