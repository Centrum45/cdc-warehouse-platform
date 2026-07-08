package com.example.warehouse.service;

import com.example.warehouse.model.CommandResult;
import com.example.warehouse.model.DashboardSnapshot;
import com.example.warehouse.model.ServiceStatus;
import com.example.warehouse.model.TableMetadata;
import com.example.warehouse.model.TableStorageView;
import com.example.warehouse.model.WarehouseLayerView;
import com.example.warehouse.model.WarehouseTableView;
import java.io.BufferedReader;
import java.io.File;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.util.stream.Stream;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.TreeSet;
import org.springframework.stereotype.Service;

@Service
public class DashboardService {
    private static final List<String> DATA_LAYERS = Arrays.asList("ods_binlog", "ods", "dim", "dwd", "dws", "dwt", "ads");
    private static final long WAREHOUSE_CACHE_MILLIS = 30000L;

    private final CommandExecutorService commandExecutorService;
    private List<WarehouseLayerView> cachedWarehouseLayers = new ArrayList<>();
    private String cachedWarehouseListing = "";
    private long cachedWarehouseAt = 0L;
    private List<TableStorageView> cachedTableStorage = new ArrayList<>();
    private String cachedTableStorageKey = "";
    private long cachedTableStorageAt = 0L;

    public DashboardService(CommandExecutorService commandExecutorService) {
        this.commandExecutorService = commandExecutorService;
    }

    public DashboardSnapshot snapshot(List<TableMetadata> tables) {
        DashboardSnapshot snapshot = new DashboardSnapshot();
        String containerStatus = readOpsFile("container_status.txt", Arrays.asList("docker", "ps", "--format", "table {{.Names}}\\t{{.Status}}\\t{{.Ports}}"));
        String warehouseListing = readOpsFile("hdfs_warehouse_ls.txt", Arrays.asList("docker", "exec", "cdc-warehouse-hdfs-namenode", "hdfs", "dfs", "-ls", "-R", "/warehouse"));
        snapshot.setContainerStatus(containerStatus);
        snapshot.setKafkaTopics(readOpsFile("kafka_topics.txt", Arrays.asList("docker", "exec", "cdc-warehouse-kafka", "kafka-topics", "--bootstrap-server", "kafka:9092", "--list")));
        snapshot.setMaxwellLogs(readOpsFile("maxwell.log", Arrays.asList("docker", "logs", "--tail", "120", "cdc-warehouse-maxwell")));
        snapshot.setKafkaLogs(readOpsFile("kafka.log", Arrays.asList("docker", "logs", "--tail", "80", "cdc-warehouse-kafka")));
        snapshot.setSparkStreamingLogs(readOpsFile("spark_streaming.log", Arrays.asList("docker", "logs", "--tail", "80", "cdc-warehouse-spark-streaming")));
        snapshot.setSparkSqlMergeLogs(readOpsFile("spark_sql_merge.log", null));
        snapshot.setAdminLogs(readOpsFile("admin.log", Arrays.asList("docker", "logs", "--tail", "80", "cdc-warehouse-admin")));
        snapshot.setHdfsWarehouseListing(warehouseListing);
        snapshot.setHdfsNamenodeLogs(readOpsFile("hdfs_namenode.log", Arrays.asList("docker", "logs", "--tail", "80", "cdc-warehouse-hdfs-namenode")));
        snapshot.setHiveDatabases(readOpsFile("hive_databases.txt", Arrays.asList("docker", "exec", "cdc-warehouse-hive-server", "beeline", "-u", "jdbc:hive2://localhost:10000", "-e", "show databases;")));
        snapshot.setHiveServerLogs(readOpsFile("hive_server.log", Arrays.asList("docker", "logs", "--tail", "80", "cdc-warehouse-hive-server")));
        snapshot.setRefreshedAt(readOpsFile("refreshed_at.txt", null));
        snapshot.setServiceStatuses(parseServiceStatuses(containerStatus));
        snapshot.setWarehouseLayers(buildWarehouseLayers(warehouseListing));
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

    private synchronized List<TableStorageView> buildStorageViews(List<TableMetadata> tables) {
        String tableKey = tableStorageKey(tables);
        long now = System.currentTimeMillis();
        if (tableKey.equals(cachedTableStorageKey) && now - cachedTableStorageAt < WAREHOUSE_CACHE_MILLIS) {
            return cachedTableStorage;
        }
        List<TableStorageView> views = new ArrayList<>();
        for (TableMetadata table : tables) {
            TableStorageView view = new TableStorageView();
            view.setDatabaseName(table.getDatabaseName());
            view.setTableName(table.getTableName());

            String binlogHdfsDir = latestHdfsPartitionPath("ods_binlog", table.getDatabaseName(), table.getTableName());
            String odsHdfsDir = latestHdfsPartitionPath("ods", table.getDatabaseName(), table.getTableName());
            if (binlogHdfsDir != null || odsHdfsDir != null) {
                view.setOdsBinlogPath(binlogHdfsDir == null ? "not generated" : binlogHdfsDir);
                view.setOdsPath(odsHdfsDir == null ? "not generated" : odsHdfsDir);
                view.setOdsBinlogSample(readHdfsHead(binlogHdfsDir, 5));
                view.setOdsSample(readHdfsHead(odsHdfsDir, 8));
            } else {
                File binlogFile = latestFile("ods_binlog", table.getDatabaseName(), table.getTableName(), "jsonl");
                File odsFile = latestFile("ods", table.getDatabaseName(), table.getTableName(), "csv");
                view.setOdsBinlogPath(displayPath(binlogFile));
                view.setOdsPath(displayPath(odsFile));
                view.setOdsBinlogSample(readHead(binlogFile, 5));
                view.setOdsSample(readHead(odsFile, 8));
            }
            views.add(view);
        }
        cachedTableStorageKey = tableKey;
        cachedTableStorageAt = now;
        cachedTableStorage = views;
        return views;
    }

    private String tableStorageKey(List<TableMetadata> tables) {
        StringBuilder builder = new StringBuilder();
        for (TableMetadata table : tables) {
            builder.append(table.getDatabaseName()).append('.').append(table.getTableName()).append(';');
        }
        builder.append(stableHdfsListingKey(readOpsFile("hdfs_warehouse_ls.txt", null)));
        return builder.toString();
    }

    private List<ServiceStatus> parseServiceStatuses(String containerStatus) {
        List<ServiceStatus> statuses = new ArrayList<>();
        if (containerStatus == null || containerStatus.trim().isEmpty()) {
            return statuses;
        }
        for (String line : containerStatus.split("\\R")) {
            String trimmed = line.trim();
            if (trimmed.isEmpty() || trimmed.startsWith("NAMES") || trimmed.startsWith("command failed")) {
                continue;
            }
            String[] parts = trimmed.split("\\s{2,}", 3);
            if (parts.length < 2) {
                continue;
            }
            ServiceStatus status = new ServiceStatus();
            status.setName(parts[0]);
            status.setStatus(parts[1]);
            status.setPorts(parts.length > 2 ? parts[2] : "");
            status.setRunning(parts[1].startsWith("Up"));
            statuses.add(status);
        }
        return statuses;
    }

    private synchronized List<WarehouseLayerView> buildWarehouseLayers(String listing) {
        long now = System.currentTimeMillis();
        String normalizedListing = stableHdfsListingKey(listing);
        if (normalizedListing.equals(cachedWarehouseListing) && now - cachedWarehouseAt < WAREHOUSE_CACHE_MILLIS) {
            return cachedWarehouseLayers;
        }
        Map<String, WarehouseTableView> tableMap = new LinkedHashMap<>();
        for (HdfsEntry entry : parseHdfsEntries(listing)) {
            WarehouseTableView table = tableFromPath(entry.path);
            if (table == null) {
                continue;
            }
            String key = table.getLayer() + "/" + table.getTable();
            WarehouseTableView existing = tableMap.get(key);
            if (existing == null) {
                existing = table;
                existing.setHdfs(true);
                tableMap.put(key, existing);
            }
            String partition = partitionFromPath(entry.path);
            if (partition != null && !existing.getPartitions().contains(partition)) {
                existing.getPartitions().add(partition);
            }
        }

        if (tableMap.isEmpty()) {
            tableMap.putAll(buildLocalWarehouseTables());
        }

        Map<String, WarehouseLayerView> layers = new LinkedHashMap<>();
        for (String layer : DATA_LAYERS) {
            WarehouseLayerView view = new WarehouseLayerView();
            view.setLayer(layer);
            layers.put(layer, view);
        }

        for (WarehouseTableView table : tableMap.values()) {
            Collections.sort(table.getPartitions());
            if (!table.getPartitions().isEmpty()) {
                table.setLatestPartition(table.getPartitions().get(table.getPartitions().size() - 1));
                table.setLatestPath(pathForLatestPartition(table));
                table.setSamplePath(table.getLatestPath());
                if (table.isHdfs()) {
                    table.setSample(readHdfsHead(table.getLatestPath(), 8));
                    table.setRowCount(countHdfsRows(table.getLatestPath()));
                } else {
                    File latest = new File(table.getLatestPath());
                    table.setSample(readHead(firstDataFile(latest), 8));
                    table.setRowCount(countLocalRows(firstDataFile(latest)));
                }
            }
            WarehouseLayerView layerView = layers.get(table.getLayer());
            if (layerView == null) {
                layerView = new WarehouseLayerView();
                layerView.setLayer(table.getLayer());
                layers.put(table.getLayer(), layerView);
            }
            layerView.getTables().add(table);
        }

        List<WarehouseLayerView> result = new ArrayList<>();
        for (WarehouseLayerView layer : layers.values()) {
            int partitionCount = 0;
            layer.getTables().sort(Comparator.comparing(WarehouseTableView::getTable));
            for (WarehouseTableView table : layer.getTables()) {
                partitionCount += table.getPartitions().size();
            }
            layer.setTableCount(layer.getTables().size());
            layer.setPartitionCount(partitionCount);
            result.add(layer);
        }
        cachedWarehouseListing = normalizedListing;
        cachedWarehouseAt = now;
        cachedWarehouseLayers = result;
        return result;
    }

    private List<HdfsEntry> parseHdfsEntries(String listing) {
        List<HdfsEntry> entries = new ArrayList<>();
        if (listing == null) {
            return entries;
        }
        for (String line : listing.split("\\R")) {
            String trimmed = line.trim();
            if (!trimmed.startsWith("d") && !trimmed.startsWith("-")) {
                continue;
            }
            String[] parts = trimmed.split("\\s+");
            if (parts.length < 8) {
                continue;
            }
            String path = parts[parts.length - 1];
            if (!path.startsWith("/warehouse/")) {
                continue;
            }
            entries.add(new HdfsEntry(trimmed.startsWith("d"), path));
        }
        return entries;
    }

    private String stableHdfsListingKey(String listing) {
        StringBuilder builder = new StringBuilder();
        for (HdfsEntry entry : parseHdfsEntries(listing)) {
            builder.append(entry.directory ? 'd' : 'f').append(':').append(entry.path).append('\n');
        }
        return builder.toString();
    }

    private WarehouseTableView tableFromPath(String path) {
        String[] parts = path.split("/");
        if (parts.length < 4 || !"warehouse".equals(parts[1])) {
            return null;
        }
        String layer = parts[2];
        if (!DATA_LAYERS.contains(layer)) {
            return null;
        }
        WarehouseTableView table = new WarehouseTableView();
        table.setLayer(layer);
        if (parts[3].startsWith("db=") && parts.length < 5) {
            return null;
        }
        if (parts.length >= 5 && parts[3].startsWith("db=") && parts[4].startsWith("table=")) {
            table.setTable(parts[3].substring(3) + "." + parts[4].substring(6));
            return table;
        }
        if (parts.length >= 4 && !parts[3].startsWith("db=") && !parts[3].startsWith("dt=")) {
            table.setTable(parts[3]);
            return table;
        }
        return null;
    }

    private String partitionFromPath(String path) {
        for (String part : path.split("/")) {
            if (part.startsWith("dt=")) {
                return part.substring(3);
            }
        }
        return null;
    }

    private String pathForLatestPartition(WarehouseTableView table) {
        String partition = table.getLatestPartition();
        if (partition == null) {
            return "";
        }
        if (table.isHdfs()) {
            if (table.getTable().contains(".")) {
                String[] names = table.getTable().split("\\.", 2);
                return "/warehouse/" + table.getLayer() + "/db=" + names[0] + "/table=" + names[1] + "/dt=" + partition;
            }
            return "/warehouse/" + table.getLayer() + "/" + table.getTable() + "/dt=" + partition;
        }
        return new File(commandExecutorService.getProjectRoot(), "data/lake/" + table.getLayer() + "/" + localTablePath(table.getTable()) + "/dt=" + partition).getPath();
    }

    private Map<String, WarehouseTableView> buildLocalWarehouseTables() {
        Map<String, WarehouseTableView> tableMap = new LinkedHashMap<>();
        File lake = new File(commandExecutorService.getProjectRoot(), "data/lake");
        for (String layer : DATA_LAYERS) {
            File layerDir = new File(lake, layer);
            if (!layerDir.exists()) {
                continue;
            }
            for (File tableDir : listLocalTables(layerDir)) {
                WarehouseTableView table = new WarehouseTableView();
                table.setLayer(layer);
                table.setTable(localDisplayName(layerDir, tableDir));
                table.setHdfs(false);
                TreeSet<String> partitions = new TreeSet<>();
                File[] dirs = tableDir.listFiles(File::isDirectory);
                if (dirs != null) {
                    for (File dir : dirs) {
                        if (dir.getName().startsWith("dt=")) {
                            partitions.add(dir.getName().substring(3));
                        }
                    }
                }
                table.setPartitions(new ArrayList<>(partitions));
                tableMap.put(layer + "/" + table.getTable(), table);
            }
        }
        return tableMap;
    }

    private List<File> listLocalTables(File layerDir) {
        List<File> tables = new ArrayList<>();
        File[] children = layerDir.listFiles(File::isDirectory);
        if (children == null) {
            return tables;
        }
        for (File child : children) {
            if (child.getName().startsWith("db=")) {
                File[] tableDirs = child.listFiles(file -> file.isDirectory() && file.getName().startsWith("table="));
                if (tableDirs != null) {
                    tables.addAll(Arrays.asList(tableDirs));
                }
            } else {
                tables.add(child);
            }
        }
        return tables;
    }

    private String localDisplayName(File layerDir, File tableDir) {
        File parent = tableDir.getParentFile();
        if (parent != null && parent.getName().startsWith("db=") && parent.getParentFile().equals(layerDir)) {
            return parent.getName().substring(3) + "." + tableDir.getName().substring(6);
        }
        return tableDir.getName();
    }

    private String localTablePath(String table) {
        if (table.contains(".")) {
            String[] parts = table.split("\\.", 2);
            return "db=" + parts[0] + "/table=" + parts[1];
        }
        return table;
    }

    private String latestHdfsPartitionPath(String layer, String database, String table) {
        String listing = readOpsFile("hdfs_warehouse_ls.txt", null);
        String prefix = "/warehouse/" + layer + "/db=" + database + "/table=" + table + "/dt=";
        String latest = null;
        for (HdfsEntry entry : parseHdfsEntries(listing)) {
            if (entry.path.startsWith(prefix)) {
                String partition = partitionFromPath(entry.path);
                if (partition != null && (latest == null || partition.compareTo(latest) > 0)) {
                    latest = partition;
                }
            }
        }
        return latest == null ? null : prefix + latest;
    }

    private String readHdfsHead(String directory, int limit) {
        if (directory == null || directory.trim().isEmpty()) {
            return "";
        }
        CommandResult result = commandExecutorService.run(Arrays.asList(
                "docker", "exec", "cdc-warehouse-hdfs-namenode",
                "sh", "-lc", "hdfs dfs -cat '" + directory + "'/* 2>/dev/null | grep -v 'NativeCodeLoader' | head -" + limit), 10);
        if (result.getExitCode() != 0) {
            return result.getOutput();
        }
        return result.getOutput();
    }

    private long countHdfsRows(String directory) {
        if (directory == null || directory.trim().isEmpty()) {
            return 0L;
        }
        CommandResult result = commandExecutorService.run(Arrays.asList(
                "docker", "exec", "cdc-warehouse-hdfs-namenode",
                "sh", "-lc", "hdfs dfs -cat '" + directory + "'/* 2>/dev/null | grep -v 'NativeCodeLoader' | wc -l"), 10);
        if (result.getExitCode() != 0) {
            return 0L;
        }
        try {
            return Long.parseLong(result.getOutput().trim());
        } catch (Exception ex) {
            return 0L;
        }
    }

    private File firstDataFile(File directory) {
        if (directory == null || !directory.exists()) {
            return null;
        }
        File[] files = directory.listFiles((dir, name) -> !name.startsWith("_") && !name.startsWith(".") && !name.endsWith(".crc"));
        if (files == null || files.length == 0) {
            return null;
        }
        Arrays.sort(files, Comparator.comparing(File::getName));
        return files[0];
    }

    private long countLocalRows(File file) {
        if (file == null || !file.exists()) {
            return 0L;
        }
        try (Stream<String> lines = Files.lines(file.toPath(), StandardCharsets.UTF_8)) {
            return lines.count();
        } catch (Exception ex) {
            return 0L;
        }
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

    private static class HdfsEntry {
        private final boolean directory;
        private final String path;

        private HdfsEntry(boolean directory, String path) {
            this.directory = directory;
            this.path = path;
        }
    }
}
