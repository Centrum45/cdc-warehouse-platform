package com.example.warehouse.service;

import com.example.warehouse.model.ReplayRequest;
import com.example.warehouse.repository.ReplayRepository;
import org.springframework.stereotype.Service;

@Service
public class ReplayService {
    private final ReplayRepository replayRepository;

    public ReplayService(ReplayRepository replayRepository) {
        this.replayRepository = replayRepository;
    }

    public String buildBootstrapCommand(ReplayRequest request) {
        String command = "maxwell-bootstrap --database " + request.getDatabaseName()
                + " --table " + request.getTableName()
                + " --from " + request.getStartTime()
                + " --to " + request.getEndTime();
        replayRepository.save(request, command);
        return command;
    }
}
