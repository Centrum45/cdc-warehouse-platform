package com.example.warehouse.controller;

import com.example.warehouse.service.DashboardService;
import com.example.warehouse.service.MetadataService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;

@Controller
@Tag(name = "Logs", description = "Runtime log viewer")
public class LogController {
    private final DashboardService dashboardService;
    private final MetadataService metadataService;

    public LogController(DashboardService dashboardService, MetadataService metadataService) {
        this.dashboardService = dashboardService;
        this.metadataService = metadataService;
    }

    @GetMapping("/logs")
    @Operation(summary = "View platform logs")
    public String logs(Model model) {
        model.addAttribute("dashboard", dashboardService.snapshot(metadataService.listTables()));
        return "logs";
    }
}
