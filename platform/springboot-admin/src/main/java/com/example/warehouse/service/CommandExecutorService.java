package com.example.warehouse.service;

import com.example.warehouse.model.CommandResult;
import java.io.BufferedReader;
import java.io.File;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.concurrent.TimeUnit;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

@Service
public class CommandExecutorService {
    private final String projectRoot;

    public CommandExecutorService(@Value("${warehouse.project-root:../..}") String projectRoot) {
        this.projectRoot = projectRoot;
    }

    public File getProjectRoot() {
        return new File(projectRoot);
    }

    public CommandResult run(List<String> command, long timeoutSeconds) {
        StringBuilder output = new StringBuilder();
        try {
            ProcessBuilder builder = new ProcessBuilder(command);
            builder.directory(new File(projectRoot));
            builder.redirectErrorStream(true);
            Process process = builder.start();
            try (BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream(), StandardCharsets.UTF_8))) {
                String line;
                while ((line = reader.readLine()) != null) {
                    output.append(line).append('\n');
                }
            }
            boolean finished = process.waitFor(timeoutSeconds, TimeUnit.SECONDS);
            if (!finished) {
                process.destroyForcibly();
                return new CommandResult(124, output.append("command timeout").toString());
            }
            return new CommandResult(process.exitValue(), output.toString());
        } catch (Exception ex) {
            return new CommandResult(1, ex.getMessage());
        }
    }
}
