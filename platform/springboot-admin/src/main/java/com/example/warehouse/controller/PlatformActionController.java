package com.example.warehouse.controller;

import com.example.warehouse.model.ActionRequest;
import com.example.warehouse.model.ActionAudit;
import com.example.warehouse.model.CommandResult;
import com.example.warehouse.repository.ActionAuditRepository;
import com.example.warehouse.service.PlatformActionService;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import java.security.Principal;
import java.util.List;
import javax.servlet.http.HttpServletRequest;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/actions")
@Tag(name = "Platform Actions", description = "Run local warehouse operation actions")
public class PlatformActionController {
    private final PlatformActionService platformActionService;
    private final ActionAuditRepository actionAuditRepository;
    private final ObjectMapper objectMapper;

    public PlatformActionController(PlatformActionService platformActionService,
                                    ActionAuditRepository actionAuditRepository,
                                    ObjectMapper objectMapper) {
        this.platformActionService = platformActionService;
        this.actionAuditRepository = actionAuditRepository;
        this.objectMapper = objectMapper;
    }

    @PostMapping("/{action}")
    @Operation(summary = "Run a local warehouse operation")
    public CommandResult run(@PathVariable String action,
                             @RequestBody(required = false) ActionRequest request,
                             HttpServletRequest httpRequest,
                             Principal principal) {
        long startedAt = System.currentTimeMillis();
        CommandResult result;
        try {
            result = platformActionService.run(action, request);
        } catch (RuntimeException ex) {
            long durationMs = System.currentTimeMillis() - startedAt;
            actionAuditRepository.save(
                    action,
                    operator(principal),
                    clientIp(httpRequest),
                    toJson(request),
                    -1,
                    ex.getMessage(),
                    durationMs
            );
            throw ex;
        }
        long durationMs = System.currentTimeMillis() - startedAt;
        actionAuditRepository.save(
                action,
                operator(principal),
                clientIp(httpRequest),
                toJson(request),
                result.getExitCode(),
                result.getOutput(),
                durationMs
        );
        return result;
    }

    @GetMapping("/audits")
    @Operation(summary = "List latest operation audit records")
    public List<ActionAudit> audits() {
        return actionAuditRepository.findLatest(50);
    }

    private String operator(Principal principal) {
        if (principal == null || principal.getName() == null || principal.getName().trim().isEmpty()) {
            return "anonymous";
        }
        return principal.getName();
    }

    private String clientIp(HttpServletRequest request) {
        String forwarded = request.getHeader("X-Forwarded-For");
        if (forwarded != null && !forwarded.trim().isEmpty()) {
            return forwarded.split(",")[0].trim();
        }
        return request.getRemoteAddr();
    }

    private String toJson(ActionRequest request) {
        if (request == null) {
            return "{}";
        }
        try {
            return objectMapper.writeValueAsString(request);
        } catch (JsonProcessingException ex) {
            return "{}";
        }
    }
}
