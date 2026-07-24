package com.example.warehouse.service;

import com.example.warehouse.model.CommandResult;
import com.example.warehouse.model.ReplayRecord;
import com.example.warehouse.model.ReplayRequest;
import com.example.warehouse.repository.ReplayRepository;
import java.util.Arrays;
import java.util.List;
import java.util.regex.Pattern;
import org.springframework.stereotype.Service;

@Service
public class ReplayService {
    private static final Pattern IDENTIFIER = Pattern.compile("[A-Za-z0-9_]+");
    private final ReplayRepository replayRepository;
    private final CommandExecutorService commandExecutorService;

    public ReplayService(ReplayRepository replayRepository,
                         CommandExecutorService commandExecutorService) {
        this.replayRepository = replayRepository;
        this.commandExecutorService = commandExecutorService;
    }

    public String buildBootstrapCommand(ReplayRequest request) {
        validate(request);
        return "python3 scripts/bootstrap_mysql_table.py metadata/tables/"
                + request.getDatabaseName() + "." + request.getTableName()
                + ".json --replace-binlog --replace-ods";
    }

    public CommandResult execute(ReplayRequest request) {
        String command = buildBootstrapCommand(request);
        long recordId = replayRepository.save(request, command);
        CommandResult result = commandExecutorService.run(
                Arrays.asList(
                        "python3",
                        "scripts/bootstrap_mysql_table.py",
                        "metadata/tables/" + request.getDatabaseName() + "." + request.getTableName() + ".json",
                        "--replace-binlog",
                        "--replace-ods"
                ),
                1800
        );
        replayRepository.updateStatus(recordId, result.getExitCode() == 0 ? "SUCCESS" : "FAILED");
        return result;
    }

    public List<ReplayRecord> latest() {
        return replayRepository.findLatest(30);
    }

    private void validate(ReplayRequest request) {
        if (request == null
                || !IDENTIFIER.matcher(value(request.getDatabaseName())).matches()
                || !IDENTIFIER.matcher(value(request.getTableName())).matches()) {
            throw new IllegalArgumentException("invalid database or table name");
        }
    }

    private String value(String value) {
        return value == null ? "" : value.trim();
    }
}
