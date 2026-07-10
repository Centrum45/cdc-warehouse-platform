package com.example.warehouse.controller;

import com.example.warehouse.model.ActionRequest;
import com.example.warehouse.model.CommandResult;
import com.example.warehouse.service.PlatformActionService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/actions")
@Tag(name = "Platform Actions", description = "Run local warehouse operation actions")
public class PlatformActionController {
    private final PlatformActionService platformActionService;

    public PlatformActionController(PlatformActionService platformActionService) {
        this.platformActionService = platformActionService;
    }

    @PostMapping("/{action}")
    @Operation(summary = "Run a local warehouse operation")
    public CommandResult run(@PathVariable String action, @RequestBody(required = false) ActionRequest request) {
        return platformActionService.run(action, request);
    }
}
