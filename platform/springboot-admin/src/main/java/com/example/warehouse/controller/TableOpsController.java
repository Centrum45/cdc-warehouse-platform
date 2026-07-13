package com.example.warehouse.controller;

import com.example.warehouse.model.CommandResult;
import com.example.warehouse.model.TableOpsRequest;
import com.example.warehouse.service.TableOpsService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.ModelAttribute;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.ResponseBody;

@Controller
@Tag(name = "Table Ops", description = "Table-level backfill, checks, and verification")
public class TableOpsController {
    private final TableOpsService tableOpsService;

    public TableOpsController(TableOpsService tableOpsService) {
        this.tableOpsService = tableOpsService;
    }

    @GetMapping("/table-ops")
    @Operation(summary = "Table operations page")
    public String page(Model model) {
        TableOpsRequest request = new TableOpsRequest();
        request.setDatabaseName("basiccomment");
        request.setTableName("avatar_commentbatchsource");
        request.setBizDt("2026-07-07");
        request.setStartDt("2026-07-07");
        request.setEndDt("2026-07-07");
        request.setDryRun(true);
        model.addAttribute("request", request);
        model.addAttribute("tables", tableOpsService.listTables());
        return "table_ops";
    }

    @PostMapping("/api/table-ops/backfill")
    @ResponseBody
    public CommandResult backfill(@ModelAttribute TableOpsRequest request) {
        return tableOpsService.backfill(request);
    }

    @PostMapping("/api/table-ops/check-lineage")
    @ResponseBody
    public CommandResult checkLineage(@ModelAttribute TableOpsRequest request) {
        return tableOpsService.checkLineage(request);
    }

    @PostMapping("/api/table-ops/consistency")
    @ResponseBody
    public CommandResult consistency(@ModelAttribute TableOpsRequest request) {
        return tableOpsService.consistency(request);
    }

    @PostMapping("/api/table-ops/onboarding-verify")
    @ResponseBody
    public CommandResult onboardingVerify(@ModelAttribute TableOpsRequest request) {
        return tableOpsService.onboardingVerify(request);
    }
}
