package com.example.warehouse.controller;

import com.example.warehouse.model.TableMetadata;
import com.example.warehouse.service.DashboardService;
import com.example.warehouse.service.MetadataService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import java.util.List;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.ResponseBody;

@Controller
@Tag(name = "Metadata", description = "Table metadata and dashboard")
public class MetadataController {
    private final MetadataService metadataService;
    private final DashboardService dashboardService;

    public MetadataController(MetadataService metadataService, DashboardService dashboardService) {
        this.metadataService = metadataService;
        this.dashboardService = dashboardService;
    }

    @GetMapping("/")
    @Operation(summary = "Dashboard home page")
    public String index(Model model) {
        List<TableMetadata> tables = metadataService.listTables();
        model.addAttribute("tables", tables);
        model.addAttribute("dashboard", dashboardService.snapshot(tables));
        return "index";
    }

    @GetMapping("/api/dashboard")
    @ResponseBody
    @Operation(summary = "Get dashboard snapshot as JSON")
    public Object dashboard() {
        return dashboardService.snapshot(metadataService.listTables());
    }

    @GetMapping("/api/metadata/tables")
    @ResponseBody
    @Operation(summary = "List onboarded table metadata")
    public List<TableMetadata> tables() {
        return metadataService.listTables();
    }

    @GetMapping("/api/metadata/tables/{databaseName}/{tableName}")
    @ResponseBody
    @Operation(summary = "Get one onboarded table metadata item")
    public ResponseEntity<TableMetadata> table(@PathVariable String databaseName, @PathVariable String tableName) {
        return metadataService.findTable(databaseName, tableName)
                .map(ResponseEntity::ok)
                .orElseGet(() -> ResponseEntity.notFound().build());
    }
}
